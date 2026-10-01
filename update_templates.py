from pathlib import Path

root = Path(r'd:\Downloads\TEST\Django-Ecommerce-master')

files = {
    'templates/base.html': '''{% load static %}
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block head_title %}Aurelia Parfums{% endblock %}</title>
  <meta name="description" content="Boutique de parfums premium, élégante et moderne.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <style>
    :root {
      --store-bg: #f7f2ee;
      --store-card: rgba(255,255,255,0.58);
      --store-ink: #1d1d1f;
      --store-muted: #6a5f5b;
      --store-gold: #c9a66b;
      --store-line: rgba(29,29,31,0.08);
      --store-shadow: 0 18px 45px rgba(24,20,17,0.06);
    }
    * { box-sizing: border-box; }
    body { background: linear-gradient(180deg,#faf7f4 0%,#f0eae5 100%); color: var(--store-ink); font-family: 'Inter', sans-serif; line-height: 1.6; }
    a { color: inherit; text-decoration: none; }
    a:hover { color: inherit; text-decoration: none; }
    img { display:block; max-width:100%; }
    h1,h2,h3,h4,h5,h6 { font-family: 'Cormorant Garamond', serif; letter-spacing: -0.04em; margin-bottom:0; }
    .container { max-width: 1240px; }
    .eyebrow { display:inline-block; margin-bottom:14px; font-size:0.72rem; font-weight:700; letter-spacing:0.15em; text-transform:uppercase; color:var(--store-muted); }
    .section-shell { padding: 80px 0; }
    .btn { display:inline-flex; align-items:center; justify-content:center; padding:0.9rem 1.5rem; border-radius:999px; font-size:0.72rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; border:1px solid transparent; transition: all 0.2s ease; }
    .btn:hover { transform: translateY(-1px); }
    .btn-primary { background: var(--store-ink); color:#fff; border-color: var(--store-ink); }
    .btn-primary:hover { background: #000; color:#fff; }
    .btn-outline-dark { background: rgba(255,255,255,0.38); color: var(--store-ink); border-color: rgba(29,29,31,0.12); }
    .btn-outline-dark:hover { background: var(--store-ink); color:#fff; }
    .product-card { display:block; background: rgba(255,255,255,0.52); border:1px solid var(--store-line); border-radius:24px; overflow:hidden; box-shadow: var(--store-shadow); transition: transform 0.25s ease; }
    .product-card:hover { transform: translateY(-4px); }
    .product-card__media { background:#efe9e2; }
    .product-card__media img { width:100%; height:310px; object-fit:cover; }
    .product-card__body { padding:22px 20px 20px; }
    .product-card__meta { display:flex; justify-content:space-between; color: var(--store-muted); font-size:0.74rem; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px; }
    .product-card__title { display:block; font-size: clamp(1.8rem, 2vw, 2.3rem); line-height:1; margin-bottom:10px; }
    .product-card__desc { color: var(--store-muted); font-size:0.97rem; line-height:1.8; }
    .product-card__row { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-top:18px; }
    .product-card__prices { display:flex; align-items:baseline; gap:10px; flex-wrap:wrap; }
    .product-card__old-price { color: var(--store-muted); text-decoration:line-through; font-size:0.88rem; }
    .product-card__price { color: var(--store-ink); font-size:1.3rem; font-weight:700; }
    .product-card__action { display:inline-flex; align-items:center; justify-content:center; min-width:110px; padding:0.8rem 1rem; border-radius:999px; background:var(--store-ink); color:#fff; font-size:0.7rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; }
    .hero { padding:32px 0 18px; }
    .hero__card { display:grid; grid-template-columns:1.15fr 0.85fr; background: linear-gradient(120deg, #efe3d8 0%, #f9f3ee 100%); border-radius:32px; box-shadow: var(--store-shadow); overflow:hidden; border:1px solid rgba(29,29,31,0.05); }
    .hero__content { padding: clamp(2rem,4vw,4rem); display:flex; flex-direction:column; justify-content:center; }
    .hero__content h1 { font-size: clamp(3.4rem, 6vw, 6rem); line-height:0.9; margin-bottom:18px; }
    .hero__content p { color: var(--store-muted); font-size:1.08rem; line-height:1.8; max-width: 540px; margin-bottom:28px; }
    .hero__actions { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:28px; }
    .hero__stats { display:flex; gap:28px; flex-wrap:wrap; }
    .hero__stat { display:flex; flex-direction:column; gap:4px; }
    .hero__stat strong { font-size:1.4rem; }
    .hero__stat span { color: var(--store-muted); font-size:0.86rem; }
    .hero__visual { min-height: 520px; background-image:url('https://images.unsplash.com/photo-1528740561666-dc2479dc08ab?auto=format&fit=crop&w=1200&q=80'); background-size:cover; background-position:center; }
    .section-header { display:flex; align-items:end; justify-content:space-between; gap:20px; flex-wrap:wrap; margin-bottom:28px; }
    .section-header h2 { font-size: clamp(2.7rem, 4vw, 4rem); line-height:0.9; }
    .cart-summary { background: rgba(255,255,255,0.55); border:1px solid rgba(29,29,31,0.06); border-radius:24px; padding:24px; }
    .checkout-card { background: rgba(255,255,255,0.55); border:1px solid rgba(29,29,31,0.06); border-radius:24px; padding:24px; }
    @media (max-width: 767px) { .hero__card { grid-template-columns:1fr; } .hero__visual { min-height: 340px; } }
  </style>
</head>
<body>
  {% include 'nav.html' %}
  <main>
    {% block content %}{% endblock %}
  </main>
  {% include 'footer.html' %}
  <script src="https://code.jquery.com/jquery-3.12.4.min.js"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.bundle.min.js"></script>
</body>
</html>
''',
    'templates/nav.html': '''{% load static %}
{% load cart_template_tags %}
{% load category_template_tags %}

<header class="store-navbar">
  <div class="container">
    <div class="store-navbar__inner">
      <a href="/" class="store-brand" aria-label="Accueil">
        <span class="store-brand__mark">A</span>
        <span class="store-brand__name">AURELIA</span>
      </a>
      <nav class="store-nav" aria-label="Navigation principale">
        <a href="/">Accueil</a>
        <a href="/shop/">Boutique</a>
        {% categories %}
        <a href="/shop/?sort=newest">Nouveautés</a>
        <a href="/shop/?q=promo">Promotions</a>
      </nav>
      <div class="store-nav-actions">
        <form class="store-search" action="{% url 'core:shop' %}" method="get">
          <i class="fa fa-search"></i>
          <input type="search" name="q" placeholder="Rechercher" value="{{ request.GET.q|default:'' }}">
        </form>
        {% if request.user.is_authenticated %}
        <a href="{% url 'core:order-summary' %}" class="store-cart" aria-label="Panier"><i class="fa fa-shopping-bag"></i><span>{{ request.user|cart_item_count }}</span></a>
        <a href="{% url 'account_logout' %}" class="store-link">Déconnexion</a>
        {% else %}
        <a href="{% url 'account_login' %}" class="store-link">Connexion</a>
        <a href="{% url 'account_signup' %}" class="btn btn-primary btn-sm">Créer un compte</a>
        {% endif %}
      </div>
    </div>
  </div>
</header>
<style>
  .store-navbar { position: sticky; top:0; z-index:50; background: rgba(247,242,238,0.9); backdrop-filter: blur(14px); border-bottom:1px solid rgba(29,29,31,0.06); }
  .store-navbar__inner { display:flex; align-items:center; justify-content:space-between; gap:16px; min-height:80px; }
  .store-brand { display:inline-flex; align-items:center; gap:12px; font-weight:700; color: var(--store-ink); }
  .store-brand__mark { display:inline-flex; align-items:center; justify-content:center; width:32px; height:32px; background:var(--store-ink); border-radius:50%; color:#fff; font-family:'Cormorant Garamond', serif; font-size:1.5rem; }
  .store-brand__name { letter-spacing:0.18em; font-size:0.82rem; }
  .store-nav { display:flex; align-items:center; gap:24px; color: var(--store-muted); font-size:0.92rem; }
  .store-nav a:hover, .store-link:hover, .store-cart:hover { color: var(--store-ink); }
  .store-nav-actions { display:flex; align-items:center; gap:16px; }
  .store-search { display:flex; align-items:center; gap:8px; min-width:200px; border:1px solid rgba(29,29,31,0.12); border-radius:999px; padding:0.65rem 0.8rem; background: rgba(255,255,255,0.42); }
  .store-search i { color: var(--store-muted); }
  .store-search input { border:0; background:transparent; outline:none; width:100%; font-size:0.94rem; }
  .store-link { color: var(--store-muted); font-weight:500; }
  .store-cart { position:relative; display:inline-flex; align-items:center; justify-content:center; width:42px; height:42px; border-radius:50%; background:rgba(255,255,255,0.6); border:1px solid rgba(29,29,31,0.08); color: var(--store-ink); }
  .store-cart span { position:absolute; top:-6px; right:-2px; min-width:18px; height:18px; border-radius:50%; background:var(--store-ink); color:#fff; font-size:0.67rem; font-weight:700; display:flex; align-items:center; justify-content:center; }
  @media (max-width: 1060px) { .store-nav { display:none; } }
  @media (max-width: 640px) { .store-search { display:none; } .store-navbar__inner { min-height:72px; } }
</style>
''',
    'templates/footer.html': '''<footer class="footer" style="padding:50px 0 24px; border-top:1px solid rgba(29,29,31,0.08); background: rgba(255,255,255,0.3);">
  <div class="container">
    <div class="row">
      <div class="col-lg-5 mb-4 mb-lg-0">
        <div style="display:inline-flex; align-items:center; gap:12px; margin-bottom:14px; font-weight:700; letter-spacing:0.18em;">
          <span style="width:34px; height:34px; display:inline-flex; align-items:center; justify-content:center; border-radius:50%; background:var(--store-ink); color:#fff; font-family:'Cormorant Garamond', serif; font-size:1.6rem;">A</span>
          <span>AURELIA</span>
        </div>
        <p style="color: var(--store-muted); line-height:1.8;">Une maison de parfum premium pensée pour les moments qui comptent. Des fragrances élégantes et durables pour chaque signature.</p>
      </div>
      <div class="col-md-4 col-lg-2 mb-4 mb-lg-0">
        <h4 style="font-size:2rem; margin-bottom:12px;">Navigation</h4>
        <ul style="list-style:none; padding:0; margin:0; color:var(--store-muted); line-height:2;">
          <li><a href="/">Accueil</a></li>
          <li><a href="/shop/">Boutique</a></li>
          <li><a href="/shop/?sort=newest">Nouveautés</a></li>
          <li><a href="/shop/?q=promo">Promotions</a></li>
        </ul>
      </div>
      <div class="col-md-4 col-lg-2 mb-4 mb-lg-0">
        <h4 style="font-size:2rem; margin-bottom:12px;">Catégories</h4>
        <ul style="list-style:none; padding:0; margin:0; color:var(--store-muted); line-height:2;">
          {% for category in categories %}
            <li><a href="/category/{{ category.slug }}/">{{ category.title }}</a></li>
          {% empty %}
            <li><a href="/shop/">Tous les parfums</a></li>
          {% endfor %}
        </ul>
      </div>
      <div class="col-md-4 col-lg-3">
        <h4 style="font-size:2rem; margin-bottom:12px;">Contact</h4>
        <ul style="list-style:none; padding:0; margin:0; color:var(--store-muted); line-height:2;">
          <li>Casablanca, Maroc</li>
          <li>+212 5 22 00 00 00</li>
          <li><a href="mailto:bonjour@aureliaparfums.ma">bonjour@aureliaparfums.ma</a></li>
          <li>Support 7j/7</li>
        </ul>
      </div>
    </div>
    <div style="display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; margin-top:36px; padding-top:18px; border-top:1px solid rgba(29,29,31,0.08); color:var(--store-muted); font-size:0.9rem;">
      <span>© 2025 Aurelia Parfums. Tous droits réservés.</span>
      <span>Livraison express • Paiement à la livraison • Qualité premium</span>
    </div>
  </div>
</footer>
''',
}

for relative_path, content in files.items():
    (root / relative_path).write_text(content, encoding='utf-8')
