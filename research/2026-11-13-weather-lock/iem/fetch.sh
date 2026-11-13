while read st off; do
 [ -s ${st,,}.csv ] || curl -s --max-time 120 "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=$st&data=tmpc&year1=2023&month1=1&day1=1&year2=2026&month2=11&day2=13&tz=Etc/UTC&format=onlycomma&latlon=no&missing=M&report_type=3" -o ${st,,}.csv
 echo "$st $(wc -l < ${st,,}.csv)"
 sleep 2
done < stations.txt
