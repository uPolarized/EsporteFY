(function () {
  async function fetchDocument(url) {
    const response = await fetch(url, {
      credentials: 'same-origin',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
      },
    });

    if (!response.ok) {
      throw new Error('Falha ao carregar proxima pagina');
    }

    const html = await response.text();
    const parser = new DOMParser();
    return parser.parseFromString(html, 'text/html');
  }

  function readNextUrl(doc) {
    const anchor = doc.querySelector('[data-infinite-scroll]');
    if (!anchor) return '';
    return anchor.getAttribute('data-next-url') || '';
  }

  function appendNewCards(targetList, doc) {
    const incomingCards = doc.querySelectorAll('.encontrar-jogadores-list .card-usuario');
    if (!incomingCards.length) {
      return 0;
    }

    const fragment = document.createDocumentFragment();
    incomingCards.forEach((card) => {
      fragment.appendChild(card);
    });
    targetList.appendChild(fragment);

    return incomingCards.length;
  }

  function initInfiniteScroll() {
    const anchor = document.querySelector('[data-infinite-scroll]');
    const list = document.querySelector('.encontrar-jogadores-list');
    if (!anchor || !list) return;

    const loader = anchor.querySelector('[data-infinite-loader]');
    const paginationNav = document.querySelector('.js-pagination');
    if (paginationNav) {
      paginationNav.style.display = 'none';
    }

    let nextUrl = anchor.getAttribute('data-next-url') || '';
    let loading = false;

    const observer = new IntersectionObserver(async (entries) => {
      const entry = entries[0];
      if (!entry || !entry.isIntersecting || loading || !nextUrl) {
        return;
      }

      loading = true;
      if (loader) loader.hidden = false;

      try {
        const doc = await fetchDocument(nextUrl);
        appendNewCards(list, doc);
        nextUrl = readNextUrl(doc);
        anchor.setAttribute('data-next-url', nextUrl);

        if (!nextUrl) {
          observer.disconnect();
          anchor.hidden = true;
        }
      } catch (error) {
        console.error('Erro no scroll infinito:', error);
      } finally {
        loading = false;
        if (loader) loader.hidden = true;
      }
    }, {
      root: null,
      rootMargin: '0px 0px 360px 0px',
      threshold: 0,
    });

    if (nextUrl) {
      observer.observe(anchor);
    } else {
      anchor.hidden = true;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initInfiniteScroll);
  } else {
    initInfiniteScroll();
  }
})();
