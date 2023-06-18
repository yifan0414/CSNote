<%*
let url = 'https://www.tianqi.com/heze/'
let res = await request({url: url,method: "GET"});
res = res.replace(/\s/g,'')
r=/<ddclass="weather">[\s\S]*?<\/dd>/g
let data = r.exec(res)[0]
r = /<span><b>(.*?)<\/b>(.*?)<\/span>/g
data = r.exec(data)
let weather='菏泽'+data[2]+data[1]
if (data[1]=='晴') weather=weather+'🔆';
else if (data[1]=='阴') weather=weather+'☁️';
-%>
<% weather %>
## Insight





## Tasks
### Overdue
```tasks
not done
due before {{date:YYYY-MM-DD}}
```

### Due today
```tasks
not done
due on {{date:YYYY-MM-DD}}
```

### Due in the next two weeks
```tasks
not done
due after {{date:YYYY-MM-DD}}
due before {{date+14d:YYYY-MM-DD}}
```

### Done today
```tasks
done on {{date:YYYY-MM-DD}}
```
