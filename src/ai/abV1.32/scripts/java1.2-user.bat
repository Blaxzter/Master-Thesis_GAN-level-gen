@echo off
set JAVA_HOME=C:\Program Files (x86)\Java\jdk1.2.2
setx JAVA_HOME "%JAVA_HOME%"
set Path=%JAVA_HOME%\bin;%Path%
echo Java 1.2 activated as user default.
