@echo off
set MAVEN_VERSION=3.9.11
set MAVEN_ROOT=%USERPROFILE%\.m2\wrapper\dists\apache-maven-%MAVEN_VERSION%
set MAVEN_HOME=%MAVEN_ROOT%\apache-maven-%MAVEN_VERSION%
if not exist "%MAVEN_HOME%\bin\mvn.cmd" (
  if not exist "%MAVEN_ROOT%" mkdir "%MAVEN_ROOT%"
  set ARCHIVE=%MAVEN_ROOT%\apache-maven-%MAVEN_VERSION%-bin.tar.gz
  if not exist "%ARCHIVE%" powershell -NoProfile -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://archive.apache.org/dist/maven/maven-3/%MAVEN_VERSION%/binaries/apache-maven-%MAVEN_VERSION%-bin.tar.gz' -OutFile '%ARCHIVE%'"
  tar -xzf "%ARCHIVE%" -C "%MAVEN_ROOT%"
)
call "%MAVEN_HOME%\bin\mvn.cmd" %*
