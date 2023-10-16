{ buildPythonApplication
, openssl
, lib
, pytest
, pytest-mock
, setuptools
}:

buildPythonApplication {
  name = "nixpkgs-merge-bot";
  src = ./.;
  format = "pyproject";
  makeWrapperArgs = [ "--prefix PATH : ${lib.makeBinPath [ openssl ]}" ];
  checkInputs = [ pytest-mock pytest openssl ];
  nativeBuildInputs = [ setuptools ];
  meta = with lib; {
    description = "A bot that merges PRs on Nixpkgs";
    homepage = "https://github.com/Mic92/nixpkgs-merge-bot";
    maintainers = with maintainers; [ mic92 lassulus ];
    license = licenses.mit;
  };
}
