with import <nixpkgs> {};
mkShell {
  packages = [
    bashInteractive
    python3
  ];
}
