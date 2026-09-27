# Use the MySQL client shipped with the selected DBngin version.
dbngin_mysql_bin="/Users/Shared/DBngin/mysql/8.4.7_arm64/bin"
if [[ -x "$dbngin_mysql_bin/mysql" ]]; then
  path=("$dbngin_mysql_bin" $path)
  typeset -U path PATH
fi
unset dbngin_mysql_bin
