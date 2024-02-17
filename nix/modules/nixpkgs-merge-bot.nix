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
      default = "/var/lib/nixpkgs-merge-bot/nixpkgs";
      description = "path to the repository";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.nixpkgs-merge-bot = {
      description = "nixpkgs-merge-bot";
      path = [
        pkgs.nix
      ];
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
        StateDirectory = "nixpkgs-merge-bot";
      };
    };
    systemd.sockets.nixpkgs-merge-bot = {
      description = "socket for nixpkgs-merge-bot";
      wantedBy = [ "sockets.target" ];
      listenStreams = [
        "/run/nixpkgs-merge-bot.sock"
      ];
    };
    services.nginx.virtualHosts.${cfg.hostname} =
      let
        ips = builtins.fromJSON (builtins.readFile ./github-webhook-ips.json);
      in
      {
        enableACME = true;
        forceSSL = true;
        locations."/" = {
          proxyPass = "http://unix:/run/nixpkgs-merge-bot.sock";
          proxyWebsockets = true;
          recommendedProxySettings = true;
          extraConfig = ''
            ${lib.concatMapStringsSep "\n" (ip: "allow ${ip};") ips}
            allow 127.0.0.1;
            allow ::1;
            # we also allow the IP of the server itself, so that can just use curl
            allow 37.27.11.42;
            allow 2a01:4f9:c012:7615::1;
            deny all;
          '';
        };
      };
  };
}
