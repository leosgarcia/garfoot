#!/usr/bin/env sh
set -eu

MAVEN_VERSION="3.9.11"
MAVEN_ROOT="${MAVEN_USER_HOME:-$HOME/.m2}/wrapper/dists/apache-maven-${MAVEN_VERSION}"
MAVEN_HOME="${MAVEN_ROOT}/apache-maven-${MAVEN_VERSION}"

if [ ! -x "${MAVEN_HOME}/bin/mvn" ]; then
  mkdir -p "${MAVEN_ROOT}"
  archive="${MAVEN_ROOT}/apache-maven-${MAVEN_VERSION}-bin.tar.gz"
  if [ ! -f "${archive}" ]; then
    curl --fail --location --silent --show-error \
      --output "${archive}" \
      "https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz"
  fi
  tar -xzf "${archive}" -C "${MAVEN_ROOT}"
fi

exec "${MAVEN_HOME}/bin/mvn" "$@"
