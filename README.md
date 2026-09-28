# Martial Dao: I Can Enhance My Talents — NovelPing RSS

This project creates an RSS feed for the NovelPing novel and automatically checks for new chapters.

## Setup

1. Create a GitHub repository, e.g. `martial-dao-novelping-rss`.
2. Upload all files from this project.
3. In GitHub, go to Settings → Pages.
4. Set Source to GitHub Actions.
5. Run the workflow once from Actions → Update NovelPing RSS → Run workflow.
6. Your RSS feed will be:

`https://YOUR-GITHUB-USERNAME.github.io/YOUR-REPOSITORY/feed.xml`

Use that URL in your RSS reader / automation service.

## Important

The feed contains links to the NovelPing chapter pages. It does not copy the novel text into the RSS feed. This is intentional: the feed acts as a chapter/update feed for an RSS consumer.

The scraper is conservative and checks sequential chapter URLs. NovelPing chapter slugs are taken from the site's chapter links when available.

## Schedule

GitHub Actions runs every 30 minutes. GitHub may delay scheduled workflows, so updates are not guaranteed to happen exactly at the scheduled minute.

You can also run it manually from the Actions tab.
