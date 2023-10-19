{ config, lib, pkgs, ... }:
let
  cfg = config.services.nixpkgs-merge-bot;
in
{
  options.services.nixpkgs-merge-bot = {
    enable = lib.mkEnableOption "Enable nixpkgs-merge-bot";
    hostname = lib.mkOption {
      type = lib.types.str;
      description = "nginx virtual host";
    };
    webhook-secret-file = lib.mkOption {
      type = lib.types.path;
      description = "path to the webhook secret file";
    };
    bot-name = lib.mkOption {
      type = lib.types.str;
      default = "nixpkgs-merge-bot";
      description = "name of the bot";
    };
    restricted-authors = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "list of restricted authors";
    };
    github-app-login = lib.mkOption {
      type = lib.types.str;
      description = "github app login";
    };
    github-app-id = lib.mkOption {
      type = lib.types.int;
      description = "github app id";
    };
    github-app-private-key-file = lib.mkOption {
      type = lib.types.path;
      description = "path to the github app private key file";
    };
    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.python3.pkgs.callPackage ../../default.nix { };
      description = "nixpkgs-merge-bot package";
    };
    repo-path = lib.mkOption {
      type = lib.types.path;
      default = "/tmp/nixpkgs";
      description = "path to the repository";
    };
  };
  # TODO: from Mic92 to lassulus
  # https://github.com/Mic92/buildbot-nix/blob/main/nix/checks/lib.nix
  # https://github.com/Mic92/buildbot-nix/blob/main/nix/checks/flake-module.nix
  # https://github.com/Mic92/buildbot-nix/blob/main/nix/checks/master.nix
  config = lib.mkIf cfg.enable {
    systemd.services.nixpkgs-merge-bot = {
      description = "nixpkgs-merge-bot";
      serviceConfig = {
        LoadCredential = [
          "webhook-secret:${cfg.webhook-secret-file}"
          "github-app-private-key:${cfg.github-app-private-key-file}"
        ];
        Restart = "on-failure";
        ExecStart = pkgs.writeShellScript "nixpkgs-merge-bot" ''
          ${lib.getExe cfg.package} \
            --webhook-secret $CREDENTIALS_DIRECTORY/webhook-secret \
            --github-app-login ${cfg.github-app-login} \
            --github-app-id ${toString cfg.github-app-id} \
            --restricted-authors "${toString cfg.restricted-authors}" \
            --github-app-private-key $CREDENTIALS_DIRECTORY/github-app-private-key \
            --repo-path ${cfg.repo-path}
        '';
      };
    };
    systemd.sockets.nixpkgs-merge-bot = {
      description = "socket for nixpkgs-merge-bot";
      wantedBy = [ "sockets.target" ];
      listenStreams = [
        "/run/nixpkgs-merge-bot.sock"
      ];
    };
    services.nginx.virtualHosts.${cfg.hostname} = {
      enableACME = true;
      forceSSL = true;
      locations."/" = {
        proxyPass = "/run/nixpkgs-merge-bot.sock";
        proxyWebsockets = true;
        recommendedProxySettings = true;
      };
    };
  };
}
