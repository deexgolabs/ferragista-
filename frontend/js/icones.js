const Icones = {
  home: '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
  users: '<circle cx="9" cy="8" r="3"/><path d="M2.5 20c0-3.6 3-6 6.5-6s6.5 2.4 6.5 6"/><circle cx="17.5" cy="9.5" r="2.3"/><path d="M16 14.3c2.4 0.2 4.6 1.9 5.5 4.2"/>',
  dollar: '<line x1="12" y1="2" x2="12" y2="22"/><path d="M17 6.5c0-1.9-2.2-3.4-5-3.4s-5 1.3-5 3.1c0 4 10 1.9 10 5.9 0 1.9-2.2 3.4-5 3.4s-5-1.5-5-3.4"/>',
  box: '<path d="M3 8l9-5 9 5-9 5-9-5z"/><path d="M3 8v9l9 5 9-5V8"/><line x1="12" y1="13" x2="12" y2="22"/>',
  barChart: '<line x1="5" y1="20" x2="5" y2="12"/><line x1="12" y1="20" x2="12" y2="6"/><line x1="19" y1="20" x2="19" y2="15"/><line x1="3" y1="20" x2="21" y2="20"/>',
  shield: '<path d="M12 3l7 3v5.5c0 4.5-3 7.7-7 9-4-1.3-7-4.5-7-9V6z"/>',
  userCircle: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="10" r="3"/><path d="M6.3 19c1-2.6 3.1-4.2 5.7-4.2s4.7 1.6 5.7 4.2"/>',
  logOut: '<path d="M9 4H5.5a2 2 0 00-2 2v12a2 2 0 002 2H9"/><line x1="15.5" y1="12" x2="21" y2="12"/><path d="M17.5 8l4 4-4 4"/>',
  menu: '<line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/>',
  wrench: '<path d="M14.7 6.3a4 4 0 10-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 005.4-5.4l-2.8 2.8-2.1-.6-.6-2.1z"/>',
  cart: '<circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M2.5 3h2.4l2.6 12.2a2 2 0 002 1.6h8.4a2 2 0 002-1.6l1.5-7.7H6"/>',
  truck: '<rect x="2.5" y="7" width="12" height="9" rx="1"/><path d="M14.5 10h3.5l3 3v3h-6.5z"/><circle cx="7" cy="18.5" r="1.6"/><circle cx="17.5" cy="18.5" r="1.6"/>',
  tag: '<path d="M12.6 2.5H5.5a1 1 0 00-1 1v7.1a1 1 0 00.3.7l9.7 9.7a1 1 0 001.4 0l7.1-7.1a1 1 0 000-1.4l-9.7-9.7a1 1 0 00-.7-.3z"/><circle cx="8.3" cy="8.3" r="1.3"/>',
  fileText: '<path d="M6 2.5h9l4 4V21a1 1 0 01-1 1H6a1 1 0 01-1-1V3.5a1 1 0 011-1z"/><line x1="8.5" y1="12" x2="15.5" y2="12"/><line x1="8.5" y1="16" x2="15.5" y2="16"/>',
  sun: '<circle cx="12" cy="12" r="4.2"/><line x1="12" y1="2.5" x2="12" y2="4.7"/><line x1="12" y1="19.3" x2="12" y2="21.5"/><line x1="4.6" y1="4.6" x2="6.1" y2="6.1"/><line x1="17.9" y1="17.9" x2="19.4" y2="19.4"/><line x1="2.5" y1="12" x2="4.7" y2="12"/><line x1="19.3" y1="12" x2="21.5" y2="12"/><line x1="4.6" y1="19.4" x2="6.1" y2="17.9"/><line x1="17.9" y1="6.1" x2="19.4" y2="4.6"/>',
  moon: '<path d="M20.5 14.5A8.5 8.5 0 019.5 3.5a8.5 8.5 0 1011 11z"/>',
  chevronDown: '<path d="M6 9l6 6 6-6"/>',
  plus: '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  trash: '<path d="M4 7h16"/><path d="M9 7V4.5a1 1 0 011-1h4a1 1 0 011 1V7"/><path d="M6 7l1 13a1 1 0 001 1h8a1 1 0 001-1l1-13"/>',
};

function svgIcone(nome, classe = "") {
  const conteudo = Icones[nome] || "";
  return `<svg class="${classe}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${conteudo}</svg>`;
}
