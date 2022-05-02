@echo off
set JAVA_HOME=C:\Program Files (x86)\Java\jdk1.3.1_28
setx JAVA_HOME "%JAVA_HOME%"
set Path=%JAVA_HOME%\bin;%Path%
echo Java 1.3 activated as user default.
