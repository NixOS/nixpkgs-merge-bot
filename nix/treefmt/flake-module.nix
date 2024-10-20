{ inputs, ... }:
{
  imports = [
    inputs.treefmt-nix.flakeModule
  ];
  perSystem =
    { pkgs, ... }:
    {
      treefmt = {
        projectRootFile = ".git/config";
        programs.nixfmt.enable = true;
        programs.shellcheck.enable = true;
        programs.deno.enable = true;
        settings.formatter.deno.excludes = [
          "tests/data/*.json"
          "secrets.yaml"
        ];
        settings.formatter.shellcheck.options = [
          "-s"
          "bash"
        ];

        programs.mypy.enable = true;
        programs.mypy.directories."." = { };
        programs.ruff.check = true;
        programs.ruff.format = true;
      };
    };
}
