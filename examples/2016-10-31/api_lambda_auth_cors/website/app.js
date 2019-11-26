window.addEventListener('load', () => {
  document.getElementById('call-api-btn').addEventListener('click', e => {
    fetch(helloWorldUrl, {
      method: 'get',
      headers: { Authorization: 'allow' }
    })
      .then(res => res.json())
      .then(resJson => alert(JSON.stringify(resJson)));
  });
});
