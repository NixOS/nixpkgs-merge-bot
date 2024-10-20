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
        settings.formatter.python = {
          command = "sh";
          options = [
            "-eucx"
            ''
              ${pkgs.ruff}/bin/ruff check --fix "$@"
              ${pkgs.python3.pkgs.black}/bin/black "$@"
            ''
            "--" # this argument is ignored by bash
          ];
          includes = [ "*.py" ];
        };
      };
    };
}
