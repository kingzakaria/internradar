"use client";

import { useMemo, useState } from "react";

type Internship = {
  id: number;
  title: string;
  company: string;
  initials: string;
  color: string;
  location: string;
  type: string;
  posted: string;
  match: number;
  category: string;
  tags: string[];
  featured?: boolean;
};

const internships: Internship[] = [
  {
    id: 1,
    title: "Product Design Intern",
    company: "Northstar Studio",
    initials: "N",
    color: "violet",
    location: "Casablanca, Morocco",
    type: "Hybrid",
    posted: "2h ago",
    match: 98,
    category: "Design",
    tags: ["Figma", "Product design", "Research"],
    featured: true,
  },
  {
    id: 2,
    title: "Frontend Engineering Intern",
    company: "Lumen Labs",
    initials: "L",
    color: "blue",
    location: "Remote · Morocco",
    type: "Remote",
    posted: "5h ago",
    match: 94,
    category: "Engineering",
    tags: ["React", "TypeScript", "CSS"],
  },
  {
    id: 3,
    title: "Growth Marketing Intern",
    company: "Goodside",
    initials: "G",
    color: "orange",
    location: "Rabat, Morocco",
    type: "On-site",
    posted: "Yesterday",
    match: 91,
    category: "Marketing",
    tags: ["Content", "Analytics", "Social"],
  },
  {
    id: 4,
    title: "Data Analyst Intern",
    company: "Atlas Finance",
    initials: "A",
    color: "green",
    location: "Casablanca, Morocco",
    type: "Hybrid",
    posted: "Yesterday",
    match: 88,
    category: "Data",
    tags: ["SQL", "Python", "Tableau"],
  },
  {
    id: 5,
    title: "People & Culture Intern",
    company: "Morrow",
    initials: "M",
    color: "pink",
    location: "Remote · Morocco",
    type: "Remote",
    posted: "2 days ago",
    match: 84,
    category: "People",
    tags: ["Recruiting", "Communication", "HR"],
  },
];

const categories = ["All roles", "Design", "Engineering", "Marketing", "Data", "People"];

function Icon({
  name,
  size = 18,
}: {
  name: "grid" | "search" | "bookmark" | "bell" | "settings" | "help" | "arrow" | "pin" | "clock" | "spark" | "chevron" | "sliders" | "plus" | "close";
  size?: number;
}) {
  const paths: Record<typeof name, React.ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
    search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
    bookmark: <path d="M6 4.75A1.75 1.75 0 0 1 7.75 3h8.5A1.75 1.75 0 0 1 18 4.75V21l-6-4-6 4z" />,
    bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" /><path d="M10 21h4" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.7a8 8 0 0 1-1.5.9l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.5-.9l-1.7.7-1.4-2.4 1.4-1.1a7 7 0 0 1 0-1.8l-1.4-1.1 1.4-2.4 1.7.7a8 8 0 0 1 1.5-.9l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.5.9l1.7-.7 1.4 2.4-1.4 1.1a7 7 0 0 1 0 1.8Z" /></>,
    help: <><circle cx="12" cy="12" r="9" /><path d="M9.6 9a2.5 2.5 0 1 1 4.4 1.6c-1.1 1.2-2 1.4-2 3" /><path d="M12 17.5h.01" /></>,
    arrow: <><path d="M7 17 17 7" /><path d="M7 7h10v10" /></>,
    pin: <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    spark: <><path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3Z" /><path d="m19 14 1 2.5 2.5 1-2.5 1L19 21l-1-2.5-2.5-1 2.5-1 1-2.5Z" /></>,
    chevron: <path d="m9 18 6-6-6-6" />,
    sliders: <><path d="M4 7h9m4 0h3M4 17h3m4 0h9" /><circle cx="15" cy="7" r="2" /><circle cx="9" cy="17" r="2" /></>,
    plus: <><path d="M12 5v14M5 12h14" /></>,
    close: <><path d="m18 6-12 12M6 6l12 12" /></>,
  };

  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  );
}

function CompanyMark({ job }: { job: Internship }) {
  return <div className={`company-mark ${job.color}`} aria-hidden="true">{job.initials}</div>;
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All roles");
  const [location, setLocation] = useState("Anywhere");
  const [saved, setSaved] = useState<number[]>([4]);
  const [showSavedOnly, setShowSavedOnly] = useState(false);
  const [sortOrder, setSortOrder] = useState<"match" | "newest">("match");
  const [alertCreated, setAlertCreated] = useState(false);

  const visibleJobs = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const filteredJobs = internships.filter((job) => {
      const matchesQuery =
        !normalizedQuery ||
        `${job.title} ${job.company} ${job.location} ${job.tags.join(" ")}`
          .toLowerCase()
          .includes(normalizedQuery);
      const matchesCategory = category === "All roles" || job.category === category;
      const matchesLocation =
        location === "Anywhere" ||
        (location === "Remote" ? job.type === "Remote" : job.location.includes(location));
      const matchesSaved = !showSavedOnly || saved.includes(job.id);
      return matchesQuery && matchesCategory && matchesLocation && matchesSaved;
    });
    return sortOrder === "match"
      ? filteredJobs.sort((first, second) => second.match - first.match)
      : filteredJobs.sort((first, second) => first.id - second.id);
  }, [category, location, query, saved, showSavedOnly, sortOrder]);

  function toggleSaved(id: number) {
    setSaved((current) =>
      current.includes(id) ? current.filter((savedId) => savedId !== id) : [...current, id],
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" aria-label="InternRadar home">
          <span className="brand-icon"><Icon name="spark" size={20} /></span>
          <span>intern<span className="brand-light">radar</span></span>
        </a>

        <div className="workspace-label">WORKSPACE</div>
        <nav className="main-nav" aria-label="Main navigation">
          <a className={`nav-link ${showSavedOnly ? "" : "active"}`} href="#opportunities" onClick={() => setShowSavedOnly(false)}><Icon name="grid" /><span>Discover</span></a>
          <button className={`nav-link ${showSavedOnly ? "active" : ""}`} onClick={() => setShowSavedOnly((value) => !value)}>
            <Icon name="bookmark" /><span>Saved jobs</span><span className="nav-count">{saved.length}</span>
          </button>
          <a className="nav-link" href="#alerts"><Icon name="bell" /><span>Job alerts</span><span className="nav-dot" /></a>
        </nav>

        <div className="sidebar-spacer" />
        <div className="profile-card">
          <div className="profile-avatar">ZO</div>
          <div className="profile-details"><strong>Zaka.O</strong><span>Student account</span></div>
          <button className="icon-button profile-menu" aria-label="Profile settings"><Icon name="settings" size={17} /></button>
        </div>
        <button className="sidebar-help"><Icon name="help" size={17} />Help & feedback</button>
        <div className="sidebar-footer">Made for your next big thing <span>✳</span></div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><Icon name="chevron" size={14} /><strong>Discover</strong></div>
          <div className="topbar-actions">
            <span className="updated-note"><span className="live-dot" />Updated just now</span>
            <button className="icon-button notification-button" aria-label="Notifications"><Icon name="bell" size={19} /><span /></button>
            <div className="top-avatar">ZO</div>
          </div>
        </header>

        <div className="content-wrap">
          <section className="welcome-row">
            <div>
              <div className="eyebrow"><span className="eyebrow-line" />YOUR NEXT CHAPTER STARTS HERE</div>
              <h1>Find work that <span>finds you.</span></h1>
              <p className="welcome-copy">A little closer to the career you have in mind.</p>
            </div>
            <div className="welcome-decoration" aria-hidden="true">
              <div className="orbit orbit-one" /><div className="orbit orbit-two" />
              <span className="decoration-spark">✳</span><span className="decoration-dot" />
            </div>
          </section>

          <section className="stats-row" aria-label="Your job search overview">
            <div className="stat-card">
              <div className="stat-icon lavender"><Icon name="spark" size={17} /></div>
              <div><div className="stat-number">24<span> new</span></div><div className="stat-label">matches this week</div></div>
              <span className="stat-trend">↗ 12%</span>
            </div>
            <div className="stat-card">
              <div className="stat-icon peach"><Icon name="bookmark" size={17} /></div>
              <div><div className="stat-number">{saved.length}<span> saved</span></div><div className="stat-label">roles to come back to</div></div>
            </div>
            <div className="stat-card profile-progress-card">
              <div className="progress-ring"><span>72<small>%</small></span></div>
              <div><div className="stat-number progress-title">Your profile</div><div className="stat-label">A few more details helps</div></div>
              <button className="text-arrow" aria-label="Complete your profile"><Icon name="arrow" size={17} /></button>
            </div>
          </section>

          <section className="jobs-section" id="opportunities">
            <div className="section-heading">
              <div>
                <div className="section-title-row"><h2>Picked for you</h2><span className="result-count">{visibleJobs.length}</span></div>
                <p>Opportunities that line up with what you’re looking for.</p>
              </div>
              <button className="preferences-button"><Icon name="sliders" size={17} />Preferences</button>
            </div>

            <div className="search-panel">
              <label className="search-field">
                <Icon name="search" size={19} />
                <input
                  type="search"
                  placeholder="Role, company, or skill"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  aria-label="Search roles, companies, or skills"
                />
                {query && <button className="clear-search" onClick={() => setQuery("")} aria-label="Clear search"><Icon name="close" size={15} /></button>}
              </label>
              <div className="search-divider" />
              <label className="location-select">
                <Icon name="pin" size={18} />
                <select value={location} onChange={(event) => setLocation(event.target.value)} aria-label="Filter by location">
                  <option>Anywhere</option><option>Remote</option><option>Casablanca</option><option>Rabat</option>
                </select>
                <span className="select-chevron"><Icon name="chevron" size={14} /></span>
              </label>
              <button className="search-button" onClick={() => document.getElementById("job-results")?.scrollIntoView({ behavior: "smooth" })}>Find a role</button>
            </div>

            <div className="filter-row">
              <div className="category-tabs" role="tablist" aria-label="Filter opportunities by category">
                {categories.map((item) => (
                  <button
                    className={`category-tab ${category === item ? "selected" : ""}`}
                    key={item}
                    onClick={() => setCategory(item)}
                    role="tab"
                    aria-selected={category === item}
                  >
                    {item}
                  </button>
                ))}
              </div>
              <button
                className="sort-button"
                onClick={() => setSortOrder((current) => current === "match" ? "newest" : "match")}
                aria-label={`Sort by ${sortOrder === "match" ? "newest" : "best match"}`}
              >
                {sortOrder === "match" ? "Best match" : "Newest"} <span className="sort-chevron">⌄</span>
              </button>
            </div>

            <div className="job-list" id="job-results">
              {visibleJobs.map((job) => (
                <article className={`job-card ${job.featured ? "featured-card" : ""}`} key={job.id}>
                  <CompanyMark job={job} />
                  <div className="job-main">
                    <div className="job-title-row"><h3>{job.title}</h3>{job.featured && <span className="new-badge">JUST IN</span>}</div>
                    <div className="company-line">{job.company}<span className="company-separator">·</span><span className="job-location"><Icon name="pin" size={13} />{job.location}</span></div>
                    <div className="tag-row">{job.tags.map((tag) => <span className="skill-tag" key={tag}>{tag}</span>)}</div>
                  </div>
                  <div className="job-aside">
                    <div className="match-label"><span className="match-dot" />{job.match}% match</div>
                    <div className="job-meta"><span>{job.type}</span><span className="meta-separator">·</span><span>{job.posted}</span></div>
                    <div className="job-actions">
                      <button
                        className={`save-button ${saved.includes(job.id) ? "is-saved" : ""}`}
                        onClick={() => toggleSaved(job.id)}
                        aria-label={saved.includes(job.id) ? `Remove ${job.title} from saved jobs` : `Save ${job.title}`}
                        aria-pressed={saved.includes(job.id)}
                      ><Icon name="bookmark" size={17} /></button>
                      <a className="view-button" href="#apply">View role <Icon name="arrow" size={14} /></a>
                    </div>
                  </div>
                </article>
              ))}
              {visibleJobs.length === 0 && (
                <div className="empty-state">
                  <div className="empty-icon"><Icon name="search" size={22} /></div>
                  <h3>No roles found just yet</h3>
                  <p>Try a different search or loosen your filters to see more opportunities.</p>
                  <button onClick={() => { setQuery(""); setCategory("All roles"); setLocation("Anywhere"); setShowSavedOnly(false); }}>Clear all filters</button>
                </div>
              )}
            </div>
            <div className="list-footer"><span>Showing {visibleJobs.length} of 24 opportunities</span><button>See all opportunities <Icon name="arrow" size={15} /></button></div>
          </section>

          <section className="alert-banner" id="alerts">
            <div className="alert-icon"><Icon name="bell" size={19} /></div>
            <div className="alert-copy"><strong>Let the right role find you.</strong><span>Get a note when new internships match your interests.</span></div>
            <button className="alert-button" onClick={() => setAlertCreated((current) => !current)} aria-pressed={alertCreated}>
              <Icon name={alertCreated ? "bell" : "plus"} size={16} />
              {alertCreated ? "Alert created" : "Create a job alert"}
            </button>
          </section>
          <footer className="page-footer"><span>Thoughtful opportunities, less searching.</span><span>InternRadar <span className="footer-spark">✳</span></span></footer>
        </div>
      </main>
    </div>
  );
}
