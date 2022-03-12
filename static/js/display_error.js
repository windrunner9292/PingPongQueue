
/* window.addEventListener('load', load_json); */
//window.alert("welcome to info view page!")

function display_error(obj){
    html = ""

    if(obj.error_source == 'movie'){
        html += "<p><b>Make sure to check the following:</b></p><ul><li>The name of the movie is correctly typed.</li><li>You have the stable internet connection</li><li>You are not hungry so you can think right</li></ul>";
        document.getElementById("error_category").innerHTML = "Error while getting movie information..."
        document.getElementById("error_message").innerHTML = html
    }

    else if(obj.error_source == 'dotahero'){
        html += "<p><b>Make sure to check the following:</b></p><ul><li>The hero's name is correctly typed. (This is not a nickname, e.g., Legion Commander is the name, and her nickname is Tresdin.)</li><li>You have the stable internet connection</li><li>You are not hungry so you can think right</li></ul>";
        document.getElementById("error_category").innerHTML = "Error while getting dota hero information..."
        document.getElementById("error_message").innerHTML = html
    }

    else if(obj.error_source == 'news'){
        html += "<p><b>Make sure to check the following:</b></p><ul><li>You have the stable internet connection</li><li>You are not hungry so you can think right</li></ul>";
        document.getElementById("error_category").innerHTML = "Error while getting news information..."
        document.getElementById("error_message").innerHTML = html
    }

   
    
}






/* <!doctype html>

<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Welcome to Info Display Project</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link href="{{ url_for('static', filename = 'css/index.css')}}" rel="stylesheet" >
    <link rel="shortcut icon" href="http://www.iconj.com/ico/n/g/ngz4vimbrv.ico" type="image/x-icon" />
</head>

<body>
  <h1> Something went wrong... </h1>
  <p><b>Make sure to check the following:</b></p><ul><li>The hero's name is correctly typed. (This is not a nickname, e.g., Legion Commander is the name, and her nickname is Tresdin.)</li><li>You have the stable internet connection</li><li>You are not hungry so you can think right</li></ul>

  <p> <b>Click below to go to homepage</b> </p>

<form action="{{ url_for('index') }}" method="post">
  <input type="submit" value="submit">
</form> 

</body>
</html> */