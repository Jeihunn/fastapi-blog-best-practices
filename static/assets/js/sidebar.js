(async () => {
  // Read locale from <html lang="...">
  const locale = document.documentElement.lang;
  const categoryList = document.getElementById("sidebar-categories");
  const tagList = document.getElementById("sidebar-tags");
  const recentWrapper = document.getElementById("sidebar-recent-posts");
  const searchForm = document.getElementById("sidebar-search-form");
  const searchInput = searchForm.querySelector("input");

  // Prepopulate search input from URL
  const params = new URLSearchParams(window.location.search);
  const initialSearch = params.get("search");
  if (initialSearch) {
    searchInput.value = initialSearch;
  }

  // Determine if we're on the blogs listing page
  const isBlogPage =
    window.location.pathname === "/blogs" ||
    window.location.pathname.startsWith("/blogs?");

  try {
    // Fetch and render categories
    let res = await fetch(`${window.API_BASE}/api/v1/blogs/categories`);
    let cats = await res.json();
    cats.forEach((cat) => {
      categoryList.insertAdjacentHTML(
        "beforeend",
        `<li><a href="#" data-cat="${cat.slug}">${cat.name}</a></li>`
      );
    });

    // Fetch and render tags
    res = await fetch(`${window.API_BASE}/api/v1/blogs/tags`);
    let tags = await res.json();
    tags.forEach((t) => {
      tagList.insertAdjacentHTML(
        "beforeend",
        `<li><a href="#" data-tag="${t.slug}">${t.name}</a></li>`
      );
    });

    // Fetch and render recent posts
    res = await fetch(
      `${window.API_BASE}/api/v1/blogs?size=5&ordering=-published_at`
    );
    let recent = await res.json();
    recent.items.forEach((p) => {
      const dt = new Date(p.published_at).toLocaleDateString(locale, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
      recentWrapper.insertAdjacentHTML(
        "beforeend",
        `
        <div class="post-item">
          <img src="${p.cover_image}" alt="${p.title}" class="flex-shrink-0"/>
          <div>
            <h4><a href="/blogs/${p.slug}">${p.title}</a></h4>
            <time datetime="${p.published_at}">${dt}</time>
          </div>
        </div>`
      );
    });
  } catch (err) {
    console.error("Sidebar load error:", err);
  }

  // Sidebar filter handlers
  categoryList.addEventListener("click", (e) => {
    const a = e.target.closest("a[data-cat]");
    if (!a) return;
    e.preventDefault();
    const cat = a.dataset.cat;
    if (isBlogPage) {
      // client-side filter without reload
      const newParams = new URLSearchParams(window.location.search);
      newParams.set("category_slug", cat);
      newParams.delete("tag_slug");
      newParams.delete("search");
      newParams.set("page", 1);
      history.pushState({ page: 1 }, "", `/blogs?${newParams}`);
      window.dispatchEvent(new PopStateEvent("popstate"));
    } else {
      window.location.href = `/blogs?category_slug=${cat}`;
    }
  });

  tagList.addEventListener("click", (e) => {
    const a = e.target.closest("a[data-tag]");
    if (!a) return;
    e.preventDefault();
    const tag = a.dataset.tag;
    if (isBlogPage) {
      const newParams = new URLSearchParams(window.location.search);
      newParams.set("tag_slug", tag);
      newParams.delete("category_slug");
      newParams.delete("search");
      newParams.set("page", 1);
      history.pushState({ page: 1 }, "", `/blogs?${newParams}`);
      window.dispatchEvent(new PopStateEvent("popstate"));
    } else {
      window.location.href = `/blogs?tag_slug=${tag}`;
    }
  });

  // Search form handler
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = searchInput.value.trim();
    if (isBlogPage) {
      const newParams = new URLSearchParams();
      if (q) newParams.set("search", q);
      newParams.set("page", 1);
      history.pushState({ page: 1 }, "", `/blogs?${newParams}`);
      window.dispatchEvent(new PopStateEvent("popstate"));
    } else {
      const url = new URL(window.location.origin + "/blogs");
      if (q) url.searchParams.set("search", q);
      window.location.href = url.toString();
    }
  });
})();
