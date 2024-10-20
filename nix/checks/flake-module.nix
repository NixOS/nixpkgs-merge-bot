{ self, ... }:
{
  perSystem =
    {
      pkgs,
      lib,
      ...
    }:
    {
      checks = lib.optionalAttrs (pkgs.stdenv.isLinux) {
        test = import ./test.nix {
          # this gives us a reference to our flake but also all flake inputs
          inherit self pkgs;
        };
      };
    };
}
