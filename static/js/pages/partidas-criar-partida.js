let map, markersLayer, userMarker;
const sidebarEl = document.getElementById("lista-quadras");
const bairroSelect = document.getElementById("bairroFilter");
const locBtn = document.getElementById("btnMinhaLocalizacao");
const modalEl = document.getElementById("selecionarQuadraModal");
const toastEl = document.getElementById("toastLocalizacao");
const toastBody = toastEl.querySelector(".toast-body");

/* ==== Helper: Exibir Toast ==== */
function showToast(mensagem, cor = "linear-gradient(90deg, #ff4b4b, #ff6b6b)") {
  toastEl.style.background = cor;
  toastBody.innerHTML = mensagem;
  const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
  toast.show();
}

/* ==== Mapa ==== */
function initMap() {
  if (window.innerWidth < 768) return;
  if (map) return map;

  map = L.map("mapa-modal", {
    center: [-22.9189, -42.8239],
    zoom: 13
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
  markersLayer = L.layerGroup().addTo(map);
  return map;
}

/* ==== Buscar Quadras ==== */
async function fetchQuadras(bairro = "") {
  if (!sidebarEl) return;

  // Oculta a sidebar enquanto carrega (remove classe "ready")
  sidebarEl.parentElement.classList.remove("ready");

  // Mostra mensagem temporária
  sidebarEl.innerHTML = `
    <div class="text-center text-secondary py-4" style="opacity: 0.8;">
      <div class="spinner-border text-danger mb-2" role="status" style="width: 2rem; height: 2rem;">
        <span class="visually-hidden">Carregando...</span>
      </div>
      <p class="mt-2">Carregando quadras...</p>
    </div>
  `;

  if (markersLayer) markersLayer.clearLayers();

  const endpoint = bairro ? `/api/quadras/?bairro=${bairro}` : "/api/quadras/";
  const res = await fetch(endpoint);
  const data = await res.json();
  const quadras = data.results || data.quadras || [];

  sidebarEl.innerHTML = "";

  quadras.forEach((q) => {
    if (!q.latitude || !q.longitude) return;

    // Marcadores no mapa (apenas desktop)
    if (map && markersLayer) {
      const marker = L.marker([q.latitude, q.longitude]).addTo(markersLayer);
      marker.bindPopup(`<strong>${q.nome}</strong><br><small>${q.bairro_nome || q.bairro}</small>`);
    }

    // Cria card lateral
    const item = document.createElement("div");
    item.className = "quadra-card mb-3 p-2 border rounded bg-secondary bg-opacity-25";
    item.innerHTML = `
      <img src="${q.foto_principal_url || q.foto_url || '/static/images/default_quadra.jpg'}"
           class="w-100 mb-2 rounded" style="height:120px;object-fit:cover;">
      <h6 class="fw-bold mb-1">${q.nome}</h6>
      <p class="text-muted small mb-2">${q.bairro_nome || q.bairro || 'Sem bairro'}</p>
      <button class="btn btn-sm btn-primary w-100" 
        onclick="selecionarQuadra(${q.id}, '${q.nome.replace(/'/g, "\\'")}')">
        Selecionar esta Quadra
      </button>
    `;
    sidebarEl.appendChild(item);
  });

  if (!quadras.length) {
    sidebarEl.innerHTML = `
      <p class="text-secondary text-center py-4">Nenhuma quadra encontrada.</p>
    `;
  }

  // Mostra a sidebar suavemente após carregar
  setTimeout(() => {
    sidebarEl.parentElement.classList.add("ready");
  }, 100);

  return quadras;
}

/* ==== Selecionar Quadra ==== */
function selecionarQuadra(id, nome) {
  document.getElementById("id_quadra_display").value = nome;
  document.getElementById("id_quadra").value = id;
  bootstrap.Modal.getInstance(modalEl).hide();
}

/* ==== Geolocalização ==== */
locBtn.addEventListener("click", async () => {
  if (!navigator.geolocation) {
    showToast("⚠️ Seu navegador não suporta geolocalização.", "linear-gradient(90deg, #555, #333)");
    return;
  }

  showToast("📍 Buscando sua localização...");

  navigator.geolocation.getCurrentPosition(
    async pos => {
      const { latitude, longitude, accuracy } = pos.coords;
      const quadras = await fetchQuadras(bairroSelect.value);
      if (!quadras || !quadras.length) return;

      let maisProxima = null;
      let menorDistancia = Infinity;

      quadras.forEach(q => {
        if (q.latitude && q.longitude) {
          const dist = calcularDistancia(latitude, longitude, q.latitude, q.longitude);
          if (dist < menorDistancia) {
            menorDistancia = dist;
            maisProxima = q;
          }
        }
      });

      if (maisProxima) {
        selecionarQuadra(maisProxima.id, maisProxima.nome);
        showToast(`✅ Quadra mais próxima: ${maisProxima.nome} (${menorDistancia.toFixed(2)} km)`,
                  "linear-gradient(90deg, #28a745, #34d058)");
      } else {
        showToast("⚠️ Nenhuma quadra próxima encontrada.", "linear-gradient(90deg, #ff9800, #ffb74d)");
      }

      if (map) {
        if (userMarker) map.removeLayer(userMarker);
        userMarker = L.marker([latitude, longitude], {
          icon: L.icon({
            iconUrl: "https://cdn-icons-png.flaticon.com/512/4876/4876901.png",
            iconSize: [32, 32],
            iconAnchor: [16, 32]
          })
        }).addTo(map);
        map.setView([latitude, longitude], 14);
      }
    },
    err => {
      showToast("❌ Não foi possível obter sua localização. Selecione o bairro manualmente.",
                "linear-gradient(90deg, #dc3545, #ff6b6b)");
    },
    { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
  );
});

/* ==== Modal ==== */
modalEl.addEventListener("shown.bs.modal", () => {
  if (window.innerWidth >= 768) {
    const m = initMap();
    setTimeout(() => {
      m.invalidateSize();
      fetchQuadras();
    }, 300);
  } else {
    fetchQuadras();
  }
});

bairroSelect.addEventListener("change", () => fetchQuadras(bairroSelect.value));

/* ==== Distância ==== */
function calcularDistancia(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2)**2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}
