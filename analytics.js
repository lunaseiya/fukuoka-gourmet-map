/* アクセス解析。全ページから読み込む。
 *
 * ▼使い方(セットアップは1行だけ)
 *   Google アナリティクスでプロパティを作ると "G-XXXXXXXXXX" という測定IDが出る。
 *   それを下の GA_ID に入れて push すれば計測が始まる。
 *   **空のままなら外部スクリプトを一切読み込まず、何も送信しない**(=導入前と同じ状態)。
 *   なので測定IDが無いうちに公開しても実害はない。
 *
 * ▼なぜ入れたか
 *   マップに月何人来ているのか、収益リンクが何回押されているのかを誰も知らない状態だった。
 *   計測がないと「SEOが効いているか」「どのスポットが読まれているか」が全部推測になる。
 *
 * ▼取っているもの
 *   - ページビュー(自動)
 *   - affiliate_click … じゃらん/アソビュー/食べログ/バリューコマースのリンクを押した回数。
 *                       どのスポットのどの提携先か が分かる
 *   - spot_open       … マップでスポットのカードを開いた回数(map/index.html から呼ぶ)
 *   - contact_click   … お問い合わせへの導線を押した回数
 */
(function () {
  'use strict';

  var GA_ID = 'G-S7J35Q0HJ8';   // 2026-09-10 設定。プロパティ「ふくおか、こそだてグルメ。」

  // 送信先が未設定なら何もしない。gtag も読み込まない
  if (!GA_ID) {
    window.icTrack = function () {};
    return;
  }

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', GA_ID);

  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA_ID);
  document.head.appendChild(s);

  // 他のスクリプト(map/index.html など)から任意のイベントを送るための入口
  window.icTrack = function (name, params) {
    try { gtag('event', name, params || {}); } catch (e) {}
  };

  // ---- 提携先リンクのクリックを拾う ----
  // スポット個別ページのPRボタンも、マップのカード内のボタンも、同じ処理で拾える
  var PARTNERS = [
    ['jalan.net', 'じゃらん'],
    ['asoview.com', 'アソビュー'],
    ['tabelog.com', '食べログ'],
    ['valuecommerce.com', 'バリューコマース'],
    ['hotpepper.jp', 'ホットペッパー']
  ];

  function partnerOf(href) {
    for (var i = 0; i < PARTNERS.length; i++) {
      if (href.indexOf(PARTNERS[i][0]) !== -1) return PARTNERS[i][1];
    }
    return null;
  }

  // スポット名は、押されたリンクの近くにある見出しから拾う。
  // 個別ページは <h1>、マップのカードは .card-name / [data-spot-name] を想定
  function spotNameNear(el) {
    var c = el.closest('[data-spot-id]');
    if (c) return c.getAttribute('data-spot-name') || c.getAttribute('data-spot-id');
    var card = el.closest('.card, .spot-card, #spotCard');
    if (card) {
      var n = card.querySelector('.card-name, h2, h3');
      if (n) return n.textContent.trim().slice(0, 60);
    }
    var h1 = document.querySelector('h1');
    return h1 ? h1.textContent.trim().slice(0, 60) : '';
  }

  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest('a[href]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';

    var p = partnerOf(href);
    if (p) {
      window.icTrack('affiliate_click', {
        partner: p,
        spot: spotNameNear(a),
        page: location.pathname
      });
      return;
    }
    if (href.indexOf('contact.html') !== -1) {
      window.icTrack('contact_click', { page: location.pathname });
    }
  }, true);
})();
