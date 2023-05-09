import React, { useState } from 'react';

function App() {
  const [text, setText] = useState("");

  const handleClick = (event) => {
    event.preventDefault();
    let xml = new XMLHttpRequest();
    xml.open("POST", "http://localhost:5000/post", true)
    xml.setRequestHeader("Content-type", "application/json");
    xml.setRequestHeader("Access-Control-Allow-Origin", "*");
    xml.onreadystatechange = function () {
      if (xml.readyState === 4 && xml.status === 200) {
        // Check console to see if you data have sent
        console.log(xml.responseText);
      }
    };

    let data = JSON.stringify({ text })

    xml.send(data)
  }

  return (
    <div>
      <textarea
        placeholder='Send something to server'
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <input type="submit" value="Send" onClick={(handleClick)} />
    </div>


  )
}

export default App