with import <nixpkgs> {};
mkShell {
  packages = [
    bashInteractive
    (python3.withPackages (ps: with ps; [ flask ]))
  ];
}
