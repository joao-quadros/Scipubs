self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('fetch', (e) => {
  // O Streamlit precisa buscar os dados em tempo real, 
  // então apenas passamos a requisição adiante
  e.respondWith(fetch(e.request));
});