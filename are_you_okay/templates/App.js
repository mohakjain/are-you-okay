import React, { useState, useEffect } from 'react';

function App() {
  const [percentOkay, setPercentOkay] = useState(0);

  useEffect(() => {
    fetch('/are_you_okay').then(res => res.json()).then(data => {
      setPercentOkay(data.percentOkay);
    });
  }, []);

  return (
    <div>
      <p>You are {percentOkay}% okay.</p>
    </div>
  );
}

export default App;