#!/usr/bin/env node
/**
 * Refresh assets/recent-work/jobs.json from dropped folders.
 *
 * A new job is a directory:
 *   assets/recent-work/<slug>/before.jpg   (or .jpeg, .png, .webp)
 *   assets/recent-work/<slug>/after.jpg
 *   assets/recent-work/<slug>/job.json     optional
 *
 * job.json may set title, trade, town, beforeAlt, and afterAlt.
 * Jobs already listed with photos outside assets/recent-work/<slug>/ are kept.
 * Town stays blank unless job.json sets it. This script does not invent facts.
 */
import { readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const recentDir = path.join(root, "assets", "recent-work");
const manifestPath = path.join(recentDir, "jobs.json");
const exts = [".jpg", ".jpeg", ".png", ".webp"];

function findSide(files, side) {
  const lower = files.map((name) => name.toLowerCase());
  for (const ext of exts) {
    const index = lower.indexOf(side + ext);
    if (index !== -1) return files[index];
  }
  return "";
}

function safeSlug(name) {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name) ? name : "";
}

function asText(value, max) {
  return String(value || "")
    .replace(/[\u0000-\u001F]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, max);
}

export async function indexRecentWork() {
  const raw = JSON.parse(await readFile(manifestPath, "utf8"));
  const kept = (Array.isArray(raw.jobs) ? raw.jobs : []).filter((job) => {
    const slug = asText(job.slug, 80);
    const prefix = `assets/recent-work/${slug}/`;
    return job.before && !String(job.before).startsWith(prefix);
  });

  const entries = await readdir(recentDir, { withFileTypes: true });
  const dropped = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const slug = safeSlug(entry.name);
    if (!slug) continue;
    const dir = path.join(recentDir, entry.name);
    const files = await readdir(dir);
    const beforeFile = findSide(files, "before");
    const afterFile = findSide(files, "after");
    if (!beforeFile || !afterFile) continue;
    let meta = {};
    if (files.includes("job.json")) {
      meta = JSON.parse(await readFile(path.join(dir, "job.json"), "utf8"));
    }
    dropped.push({
      slug,
      title: asText(meta.title, 80) || slug.replace(/-/g, " "),
      trade: asText(meta.trade, 40),
      town: asText(meta.town, 40),
      before: `assets/recent-work/${slug}/${beforeFile}`,
      after: `assets/recent-work/${slug}/${afterFile}`,
      beforeAlt: asText(meta.beforeAlt, 180) || `${asText(meta.title, 80) || slug} before`,
      afterAlt: asText(meta.afterAlt, 180) || `${asText(meta.title, 80) || slug} after`,
    });
  }

  const jobs = [...kept.filter((job) => !dropped.some((item) => item.slug === job.slug)), ...dropped];
  const next = {
    note: raw.note,
    jobs,
  };
  await writeFile(manifestPath, JSON.stringify(next, null, 2) + "\n");
  return jobs;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  indexRecentWork()
    .then((jobs) => {
      console.log(`Wrote ${jobs.length} job${jobs.length === 1 ? "" : "s"} to assets/recent-work/jobs.json`);
    })
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}
