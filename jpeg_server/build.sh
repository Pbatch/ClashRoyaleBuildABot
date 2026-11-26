#!/bin/sh
# Builds clashroyalebuildabot/data/jpeg-server.jar from src/: Java compiled
# against the Android SDK's android.jar, then converted to dex with d8.
#
# Needs a JDK 17+ (set JAVAC, or have javac on the PATH) and the Android
# SDK (set ANDROID_HOME, default ~/Android/Sdk) with platforms;android-36
# and cmdline-tools installed. Users of the bot don't need any of this:
# the built jar is committed.
set -e
cd "$(dirname "$0")"
SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
JAVAC="${JAVAC:-$(command -v javac)}"
ANDROID_JAR="$SDK/platforms/android-36/android.jar"
OUT=../clashroyalebuildabot/data/jpeg-server.jar

rm -rf build && mkdir -p build/classes
"$JAVAC" --release 17 -Xlint:-options -cp "$ANDROID_JAR" -d build/classes src/*.java
JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$JAVAC")")")" \
    "$SDK/cmdline-tools/latest/bin/d8" --min-api 34 --lib "$ANDROID_JAR" \
    --output build/jpeg-server.jar $(find build/classes -name '*.class')
cp build/jpeg-server.jar "$OUT"
echo "built $OUT"
