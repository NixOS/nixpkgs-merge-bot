{
  description = "Allows package maintainers to merge in nixpkgs";

  inputs = {
    nixpkgs.url = "github:Nixos/nixpkgs/nixos-unstable-small";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";

    # used for development
    # https://github.com/numtide/treefmt-nix/pull/269
    treefmt-nix.url = "github:numtide/treefmt-nix/mypy";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";

    sops-nix.url = "github:Mic92/sops-nix";
    sops-nix.inputs.nixpkgs.follows = "nixpkgs";

    disko.url = "github:nix-community/disko";
    disko.inputs.nixpkgs.follows = "nixpkgs";

    srvos.url = "github:numtide/srvos";
    srvos.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{ self, flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } (
      { lib, ... }:
      {
        imports = [
          ./nix/checks/flake-module.nix
          ./nix/treefmt/flake-module.nix
          ./nix/modules/flake-module.nix
          ./nix/machine.nix
        ];
        systems = [
          "x86_64-linux"
          "aarch64-linux"
          "aarch64-darwin"
        ];
        perSystem =
          {
            self',
            pkgs,
            system,
            ...
          }:
          {
            packages.default = pkgs.python3.pkgs.callPackage ./default.nix { };
            devShells.default = pkgs.mkShell {
              packages =
                with pkgs;
                [
                  nixos-anywhere
                  sops
                ]
                ++ self'.packages.default.buildInputs
                ++ self'.packages.default.nativeBuildInputs;
            };
            checks =
              let
                nixosMachines = lib.mapAttrs' (
                  name: config: lib.nameValuePair "nixos-${name}" config.config.system.build.toplevel
                ) ((lib.filterAttrs (_: config: config.pkgs.system == system)) self.nixosConfigurations);
                packages = lib.mapAttrs' (n: lib.nameValuePair "package-${n}") self'.packages;
                devShells = lib.mapAttrs' (n: lib.nameValuePair "devShell-${n}") self'.devShells;
              in
              lib.optionalAttrs (pkgs.stdenv.isLinux) nixosMachines // packages // devShells;
          };
      }
    );
}
