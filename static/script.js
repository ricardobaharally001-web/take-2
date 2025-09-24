
(()=>{
  const html=document.documentElement;
  const saved=localStorage.getItem('theme');
  if(saved) html.dataset.theme=saved;
  else html.dataset.theme=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
  document.querySelector('#themeToggle')?.addEventListener('click',()=>{
    html.dataset.theme=html.dataset.theme==='dark'?'light':'dark';
    localStorage.setItem('theme',html.dataset.theme);
  });
})();
