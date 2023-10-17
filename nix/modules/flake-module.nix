{
  flake.nixosModules.nixpkgs-merge-bot = ({
    imports = [
      ./nixpkgs-merge-bot.nix
    ];
  });
}
