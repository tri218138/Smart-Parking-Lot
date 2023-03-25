import React, { useState, useEffect } from 'react';

function App() {
  const [input, setInput] = useState("");
  const [type, setType] = useState("SpaCy")
  const [ratio, setRatio] = useState("0.8")

  const handleClick = (event) => {
    event.preventDefault();
    let xml = new XMLHttpRequest();
    xml.open("POST", "http://localhost:5000/summarizer", true)
    xml.setRequestHeader("Content-type", "application/json");
    xml.setRequestHeader("Access-Control-Allow-Origin", "*");
    xml.onreadystatechange = function () {
      if (xml.readyState === 4 && xml.status === 200) {
        console.log(xml.responseText);
      }
    };

    let data = JSON.stringify({
      'input': { input },
      'type': { type },
      'ratio': { ratio }
    })

    xml.send(data)
  }

  return (
    <div>
      <textarea
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <select value={type} onChange={(e) => setType(e.target.value)}>
        <option value="SpaCy">SpaCy</option>
        <option value="NLTK">NLTK</option>
        <option value="GenSim">GenSim</option>
        <option value="Summa">GenSim</option>
      </select>

      <input type="text" value={ratio} onChange={(e) => setRatio(e.target.value)} />
      <input type="submit" value="Summarize" onClick={(handleClick)} />
    </div>


  )
}

export default App