function ajaxRequest(url) {
  const checked = document.getElementById("mycheckbox").checked;
  console.log("Sending data to the server that the checkbox is", checked);

  // Use the XMLHttpRequest API
  const xhttp = new XMLHttpRequest();
  xhttp.onload = function() {
    console.log("Result sent to server!");
  }
  xhttp.open("POST", url, true);
  xhttp.send();
}