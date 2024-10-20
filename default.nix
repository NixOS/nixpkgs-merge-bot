{
  buildPythonApplication,
  openssl,
  lib,
  pytest,
  pytest-mock,
  setuptools,
  git,
}:

buildPythonApplication {
  name = "nixpkgs-merge-bot";
  src = ./.;
  format = "pyproject";
  makeWrapperArgs = [
    "--prefix PATH : ${
      lib.makeBinPath [
        openssl
        git
      ]
    }"
  ];
  doCheck = true;
  nativeBuildInputs = [ setuptools ];
  nativeCheckInputs = [
    pytest-mock
    pytest
    openssl
    git
  ];
  checkPhase = ''
    pytest ./tests
  '';
  meta = with lib; {
    description = "A bot that merges PRs on Nixpkgs";
    homepage = "https://github.com/Mic92/nixpkgs-merge-bot";
    maintainers = with maintainers; [
      mic92
      lassulus
    ];
    license = licenses.mit;
    mainProgram = "nixpkgs-merge-bot";
  };
}
