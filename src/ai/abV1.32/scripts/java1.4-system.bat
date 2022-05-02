@echo off
set JAVA_HOME=C:\Program Files (x86)\Java\jdk1.4.2_19
setx JAVA_HOME "%JAVA_HOME%" /M
set Path=%JAVA_HOME%\bin;%Path%
echo Java 1.4 activated as system-wide default.
