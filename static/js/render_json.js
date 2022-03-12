
/* window.addEventListener('load', load_json); */
//window.alert("welcome to info view page!")

function load_json(obj){
    var type = obj["header"].type
    //window.alert(type)
    if(type == "dota hero" || type == "movie"){
        traverse_dota_or_movie(obj);
    }
    else if (type == 'news'){
        traverse_news(obj);
        reset_div_ids();
    }
}


// traverses JSON object from dota or movie submission.
function traverse_dota_or_movie(obj){
    var data = obj['data'];
    var html = "";
    for (var i = 0; i < data.length; i++) {
        if(typeof data[i]=='object'){
            for (var key in data[i]){
                if(typeof data[i][key] != 'object'){  // if key contains the value rightaway
                    html += ("<tr><td>" + key + " : </td><td>" + data[i][key] + "</td></tr>");
                }
                else{  // if key contains another set of object
                    html += ("<tr><th colspan=\"2\"><h2>" + key + "</h2></th></tr>");
                    for (var key_ in data[i][key]){
                        html += ("<tr><td>" + key_ + " : </td><td>" + data[i][key][key_]    + "</td></tr>");
                    }
                }
            }
        }
    }
    document.getElementById("json_display_dota_or_movie").innerHTML = "<TABLE BORDER=\"5\" WIDTH=\"70%\" CELLPADDING=\"4\" CELLSPACING=\"3\">" + html + "</table>";
}


// traverses JSON object from news submission.
function traverse_news(obj){
    var data = obj['data'];
    var news_count = obj["header"].number_of_news
    var html = "";
    for (var i = 0; i < data.length; i++) { // 5
        html += ("<p id=\"news_count\"> Top news #" + (i+1).toString() + " </p>");
        for (var j = 0; j < data[i].length; j++){  // 3
            if(typeof data[i][j]=='object'){
                for (var key in data[i][j]){
                    if(typeof data[i][j][key] != 'object'){  // if key contains the value rightaway
                        if(j == 2){
                            html += "<a href =\"" + data[i][j][key] +"\" class=\"news_link\">Click here to see full news</a>";
                        }
                        else{
                        html += "<div id =\"" + (j+1).toString() + "th element in news\">";
                        html += ("<p>" + data[i][j][key] + "</p>");
                        }
                    }
                    html += "</div>";
                }
            }
        }
        html += "<br><hr><br>"
    }
    
    document.getElementById("json_display_news").innerHTML = html;
}

// traverses JSON object from news submission.
function reset_div_ids(){
    while(document.getElementById("1th element in news") &&
        document.getElementById("2th element in news")){
            document.getElementById("1th element in news").setAttribute("id", "news_heading");     
            document.getElementById("2th element in news").setAttribute("id", "news_summary");
    }
}




