{
  description = "Allows package maintainers to merge in nixpkgs";

  inputs = {
    nixpkgs.url = "github:Nixos/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";

    # used for development
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs@{ self, flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } ({ lib, ... }:
      {
        imports = [
          ./nix/checks/flake-module.nix
          ./nix/treefmt/flake-module.nix
          ./nix/modules/flake-module.nix
        ];
        systems = [ "x86_64-linux" "aarch64-linux" ];
        perSystem = { self', pkgs, system, ... }: {
          packages.default = pkgs.python3.pkgs.callPackage ./default.nix { };
          checks =
            let
              nixosMachines = lib.mapAttrs' (name: config: lib.nameValuePair "nixos-${name}" config.config.system.build.toplevel) ((lib.filterAttrs (_: config: config.pkgs.system == system)) self.nixosConfigurations);
              packages = lib.mapAttrs' (n: lib.nameValuePair "package-${n}") self'.packages;
              devShells = lib.mapAttrs' (n: lib.nameValuePair "devShell-${n}") self'.devShells;
            in
            nixosMachines // packages // devShells;
        };
      });
}
