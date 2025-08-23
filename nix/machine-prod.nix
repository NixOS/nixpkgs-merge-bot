{ inputs, ... }:
{
  flake.nixosConfigurations.nixpkgs-merge-bot = inputs.nixpkgs.lib.nixosSystem {
    modules = [
      (
        { config, lib, ... }:
        {
          nixpkgs.hostPlatform = "x86_64-linux";
          users.users.root.openssh.authorizedKeys.keys = [
            "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDIb3uuMqE/xSJ7WL/XpJ6QOj4aSmh0Ga+GtmJl3CDvljGuIeGCKh7YAoqZAi051k5j6ZWowDrcWYHIOU+h0eZCesgCf+CvunlXeUz6XShVMjyZo87f2JPs2Hpb+u/ieLx4wGQvo/Zw89pOly/vqpaX9ZwyIR+U81IAVrHIhqmrTitp+2FwggtaY4FtD6WIyf1hPtrrDecX8iDhnHHuGhATr8etMLwdwQ2kIBx5BBgCoiuW7wXnLUBBVYeO3II957XP/yU82c+DjSVJtejODmRAM/3rk+B7pdF5ShRVVFyB6JJR+Qd1g8iSH+2QXLUy3NM2LN5u5p2oTjUOzoEPWZo7lykZzmIWd/5hjTW9YiHC+A8xsCxQqs87D9HK9hLA6udZ6CGkq4hG/6wFwNjSMnv30IcHZzx6IBihNGbrisrJhLxEiKWpMKYgeemhIirefXA6UxVfiwHg3gJ8BlEBsj0tl/HVARifR2y336YINEn8AsHGhwrPTBFOnBTmfA/VnP1NlWHzXCfVimP6YVvdoGCCnAwvFuJ+ZuxmZ3UzBb2TenZZOzwzV0sUzZk0D1CaSBFJUU3oZNOkDIM6z5lIZgzsyKwb38S8Vs3HYE+Dqpkfsl4yeU5ldc6DwrlVwuSIa4vVus4eWD3gDGFrx98yaqOx17pc4CC9KXk/2TjtJY5xmQ==" # lassulus
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKbBp2dH2X3dcU1zh+xW3ZsdYROKpJd3n13ssOP092qE" # Mic92
            "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBCsjXKHCkpQT4LhWIdT0vDM/E/3tw/4KHTQcdJhyqPSH0FnwC8mfP2N9oHYFa2isw538kArd5ZMo5DD1ujL5dLk= ssh@secretive.Joerg’s-Laptop.local" # Mic92
            "sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29tAAAAIP4MIZG/hZR3Ib7faGDyK67Tk53Q1P7pE5cFIWwEFbrtAAAABHNzaDo=" # Fritz Otlinghaus, Scriptkiddi
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPqY9E43rQl3MHlE9L5cAqbdtePPNZADG4LGuQyzkgh6"
          ];
          boot.loader.grub.devices = lib.mkForce [ "/dev/sda" ];

          sops.secrets."prod/webhook_secret" = { };
          sops.secrets."prod/github_app_key" = { };
          services.nixpkgs-merge-bot = {
            enable = true;
            hostname = "nixpkgs-merge-bot.nixos.org";
            github-app-login = "NixOS";
            github-app-id = 409421;
            webhook-secret-file = config.sops.secrets."prod/webhook_secret".path;
            github-app-private-key-file = config.sops.secrets."prod/github_app_key".path;
          };

          systemd.services.nixpkgs-merge-bot.environment = {
            LOGLEVEL = "DEBUG";
          };

          system.stateVersion = "23.11";

          security.acme.acceptTerms = true;
          security.acme.defaults.email = "nix@lassul.us";

          system.autoUpgrade = {
            enable = true;
            allowReboot = true;
            flake = "github:nixos/nixpkgs-merge-bot#nixpkgs-merge-bot";
            dates = "*:0/10:00";
            flags = [ "--refresh" ];
          };
        }
      )
      ./modules/nixpkgs-merge-bot.nix
      ./modules/sops.nix
      ./disk-config.nix

      inputs.sops-nix.nixosModules.sops
      inputs.disko.nixosModules.disko

      inputs.srvos.nixosModules.hardware-hetzner-cloud
      inputs.srvos.nixosModules.server
      inputs.srvos.nixosModules.mixins-nginx
    ];
  };
}
