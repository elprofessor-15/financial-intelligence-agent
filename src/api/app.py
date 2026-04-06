import os
import sqlite3
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.agents.orchestrator import FinancialAgentOrchestrator

orchestrator: FinancialAgentOrchestrator = None
DB_PATH = "data/processed/filings.db"

UI_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>fin.agent — Financial Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=Instrument+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #f4f1ea;
  --sidebar: #1e1b2e;
  --sidebar-border: #2d2a40;
  --accent: #5b4fff;
  --accent-dim: #5b4fff18;
  --green: #00c896;
  --green-dim: #00c89615;
  --amber: #f59e0b;
  --red: #ef4444;
  --text: #0f0e17;
  --text-2: #5a5870;
  --text-3: #9896a8;
  --card: #ffffff;
  --card-border: #e4e0d6;
  --pill: #eceae2;
  --font-h: 'Syne', sans-serif;
  --font-b: 'Instrument Sans', sans-serif;
  --r: 10px;
  --sh: 0 1px 3px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.04);
  --sh-lg: 0 8px 28px rgba(0,0,0,0.09);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{font-size:15px;}
body{font-family:var(--font-b);background:var(--bg);color:var(--text);display:flex;min-height:100vh;overflow-x:hidden;}

.sidebar{width:220px;min-height:100vh;background:var(--sidebar);display:flex;flex-direction:column;position:fixed;top:0;left:0;bottom:0;z-index:200;border-right:1px solid var(--sidebar-border);}
.sidebar-logo{padding:1.3rem 1.2rem 1rem;font-family:var(--font-h);font-size:1.25rem;font-weight:700;color:#fff;letter-spacing:-0.5px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--sidebar-border);}
.logo-dot{color:var(--green);}
.sidebar-user{display:flex;align-items:center;gap:10px;padding:0.9rem 1.2rem;border-bottom:1px solid var(--sidebar-border);}
.avatar{width:30px;height:30px;border-radius:7px;background:var(--accent);display:flex;align-items:center;justify-content:center;font-family:var(--font-h);font-size:0.65rem;font-weight:700;color:#fff;}
.u-name{font-size:0.8rem;font-weight:500;color:#fff;}
.u-role{font-size:0.65rem;color:#ffffff50;margin-top:1px;}
.nav-sec{padding:0.9rem 0 0.2rem;}
.nav-lbl{font-size:0.58rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#ffffff30;padding:0 1.2rem 0.35rem;}
.nl{display:flex;align-items:center;gap:9px;padding:0.52rem 1.2rem;color:#ffffff55;font-size:0.8rem;cursor:pointer;text-decoration:none;border-left:2px solid transparent;transition:all 0.14s;}
.nl:hover{color:#ffffffcc;background:#ffffff08;}
.nl.on{color:#fff;border-left-color:var(--green);background:#ffffff0a;}
.nl svg{width:14px;height:14px;flex-shrink:0;opacity:0.55;}
.nl.on svg,.nl:hover svg{opacity:1;}
.sidebar-foot{margin-top:auto;padding:0.85rem;border-top:1px solid var(--sidebar-border);display:flex;flex-direction:column;gap:2px;}

.main{margin-left:220px;flex:1;display:flex;flex-direction:column;min-height:100vh;}
.topbar{background:var(--bg);border-bottom:1px solid var(--card-border);height:52px;padding:0 1.6rem;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;}
.tb-title{font-family:var(--font-h);font-size:0.95rem;font-weight:600;}
.tb-right{display:flex;align-items:center;gap:0.6rem;}
.tb-btn{display:flex;align-items:center;gap:5px;padding:0.32rem 0.75rem;font-size:0.72rem;color:var(--text-2);border-radius:7px;cursor:pointer;border:1px solid var(--card-border);background:var(--card);transition:all 0.14s;font-family:var(--font-b);}
.tb-btn:hover{border-color:var(--accent);color:var(--accent);}
.live-pill{background:var(--green);color:#fff;font-size:0.6rem;font-weight:700;padding:2px 8px;border-radius:999px;letter-spacing:0.08em;font-family:var(--font-h);}

.body-wrap{display:flex;flex:1;}
.p-left{width:420px;flex-shrink:0;padding:1.4rem 1.1rem 1.4rem 1.6rem;display:flex;flex-direction:column;gap:0.85rem;border-right:1px solid var(--card-border);}
.p-right{flex:1;min-width:0;padding:1.4rem 1.6rem 1.4rem 1.1rem;display:flex;flex-direction:column;gap:0.85rem;overflow-y:auto;max-height:calc(100vh - 52px);}

/* Filter */
.fbar{display:flex;gap:0.4rem;flex-wrap:wrap;align-items:center;}
.sw{display:flex;align-items:center;gap:7px;background:var(--card);border:1px solid var(--card-border);border-radius:8px;padding:0.4rem 0.8rem;flex:1;min-width:160px;transition:border-color 0.14s;}
.sw:focus-within{border-color:var(--accent);}
.sw input{border:none;outline:none;font-family:var(--font-b);font-size:0.78rem;color:var(--text);background:transparent;width:100%;}
.sw input::placeholder{color:var(--text-3);}
.fp{font-family:var(--font-b);font-size:0.72rem;padding:0.34rem 0.72rem;border-radius:7px;border:1px solid var(--card-border);background:var(--card);color:var(--text-2);cursor:pointer;transition:all 0.14s;white-space:nowrap;}
.fp:hover{border-color:var(--accent);color:var(--accent);}
.fp.on{background:var(--accent);border-color:var(--accent);color:#fff;}

.sr{display:flex;align-items:center;justify-content:space-between;}
.sr-ct{font-size:0.75rem;color:var(--text-2);}
.sr-ct strong{color:var(--accent);font-weight:600;}
.srt{font-size:0.72rem;color:var(--text-2);padding:0.28rem 0.65rem;border:1px solid var(--card-border);border-radius:6px;background:var(--card);cursor:pointer;}

/* Cards */
.clist{display:flex;flex-direction:column;gap:0.55rem;overflow-y:auto;max-height:calc(100vh - 218px);}
.clist::-webkit-scrollbar{width:3px;}
.clist::-webkit-scrollbar-thumb{background:var(--card-border);border-radius:3px;}
.cc{background:var(--card);border:1px solid var(--card-border);border-radius:var(--r);padding:0.85rem 1rem;cursor:pointer;transition:all 0.16s;border-left:3px solid transparent;box-shadow:var(--sh);}
.cc:hover{box-shadow:var(--sh-lg);transform:translateY(-1px);border-color:#d5d0c6;}
.cc.sel{border-left-color:var(--accent);background:#fafaff;}
.cc-top{display:flex;align-items:center;gap:0.75rem;}
.co-logo{width:34px;height:34px;border-radius:7px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-family:var(--font-h);font-size:0.72rem;font-weight:700;border:1px solid var(--card-border);overflow:hidden;background:#f8f7f3;}
.co-logo img{width:100%;height:100%;object-fit:contain;padding:4px;}
.ci{flex:1;min-width:0;}
.ci-name{font-family:var(--font-h);font-size:0.84rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ci-sub{font-size:0.68rem;color:var(--text-2);margin-top:1px;}
.ring{width:38px;height:38px;flex-shrink:0;position:relative;display:flex;align-items:center;justify-content:center;}
.ring svg{position:absolute;top:0;left:0;transform:rotate(-90deg);}
.ring-num{font-family:var(--font-h);font-size:0.68rem;font-weight:700;color:var(--green);}
.ct{display:flex;flex-wrap:wrap;gap:0.3rem;margin-top:0.6rem;}
.tag{font-size:0.65rem;padding:0.16rem 0.5rem;border-radius:5px;border:1px solid var(--card-border);background:var(--pill);color:var(--text-2);}
.tag.g{background:var(--green-dim);border-color:#00c89628;color:var(--green);}
.tag.a{background:var(--accent-dim);border-color:#5b4fff28;color:var(--accent);}
.cf{display:flex;align-items:center;justify-content:space-between;margin-top:0.6rem;}
.cf-t{font-size:0.65rem;color:var(--text-3);}
.bm{background:none;border:none;cursor:pointer;color:var(--text-3);line-height:0;padding:1px;}
.bm:hover{color:var(--accent);}

/* Views */
.view{display:none;flex-direction:column;gap:0.85rem;}
.view.on{display:flex;}

/* Detail header */
.dh{background:var(--card);border:1px solid var(--card-border);border-radius:var(--r);padding:1.1rem;box-shadow:var(--sh);}
.dh-top{display:flex;align-items:flex-start;gap:0.85rem;margin-bottom:0.9rem;}
.dh-logo{width:48px;height:48px;border-radius:9px;border:1px solid var(--card-border);display:flex;align-items:center;justify-content:center;background:#f8f7f3;overflow:hidden;flex-shrink:0;}
.dh-logo img{width:100%;height:100%;object-fit:contain;padding:5px;}
.dh-inf{flex:1;}
.dh-name{font-family:var(--font-h);font-size:1.2rem;font-weight:700;line-height:1.2;}
.dh-sec{font-size:0.74rem;color:var(--text-2);margin-top:3px;}
.dh-bgs{display:flex;gap:0.35rem;margin-top:0.45rem;flex-wrap:wrap;}
.dh-sc{display:flex;flex-direction:column;align-items:center;flex-shrink:0;}
.dh-ring{position:relative;width:52px;height:52px;display:flex;align-items:center;justify-content:center;}
.dh-ring svg{position:absolute;top:0;left:0;transform:rotate(-90deg);}
.dh-sn{font-family:var(--font-h);font-size:0.95rem;font-weight:700;color:var(--green);}
.dh-sl{font-size:0.58rem;color:var(--green);margin-top:2px;text-align:center;}
.dh-acts{display:flex;gap:0.5rem;flex-wrap:wrap;}

.btn{display:flex;align-items:center;gap:5px;padding:0.48rem 0.9rem;border-radius:8px;font-size:0.75rem;font-weight:500;cursor:pointer;border:none;font-family:var(--font-b);transition:all 0.14s;white-space:nowrap;}
.btn-p{background:var(--accent);color:#fff;}
.btn-p:hover{background:#4a3fe0;box-shadow:0 3px 10px rgba(91,79,255,0.3);}
.btn-s{background:var(--sidebar);color:#fff;}
.btn-s:hover{background:#2a2740;}
.btn-o{background:transparent;color:var(--text);border:1px solid var(--card-border);}
.btn-o:hover{border-color:var(--accent);color:var(--accent);}

/* Stats */
.sg{display:grid;grid-template-columns:repeat(3,1fr);gap:0.65rem;}
.sc{background:var(--card);border:1px solid var(--card-border);border-radius:var(--r);padding:0.8rem 0.9rem;box-shadow:var(--sh);}
.sc-lbl{font-size:0.62rem;color:var(--text-3);text-transform:uppercase;letter-spacing:0.07em;font-weight:600;margin-bottom:0.28rem;}
.sc-val{font-family:var(--font-h);font-size:1.1rem;font-weight:700;}
.sc-sub{font-size:0.65rem;color:var(--text-2);margin-top:2px;}

/* Query box */
.qb{background:var(--card);border:1px solid var(--card-border);border-radius:var(--r);padding:1rem;box-shadow:var(--sh);}
.qb-h{font-family:var(--font-h);font-size:0.78rem;font-weight:600;margin-bottom:0.65rem;display:flex;align-items:center;gap:6px;}
.qb-sp{width:16px;height:16px;background:var(--accent);border-radius:4px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.chips{display:flex;flex-wrap:wrap;gap:0.3rem;margin-bottom:0.65rem;}
.chip{font-size:0.67rem;padding:0.22rem 0.55rem;border-radius:5px;border:1px solid var(--card-border);background:var(--pill);color:var(--text-2);cursor:pointer;transition:all 0.14s;}
.chip:hover{border-color:var(--accent);color:var(--accent);background:var(--accent-dim);}
.qta{width:100%;background:var(--bg);border:1px solid var(--card-border);border-radius:8px;padding:0.65rem 0.8rem;font-size:0.78rem;font-family:var(--font-b);color:var(--text);resize:none;outline:none;min-height:64px;line-height:1.6;transition:border-color 0.14s;}
.qta:focus{border-color:var(--accent);}
.qb-ft{display:flex;align-items:center;justify-content:space-between;margin-top:0.5rem;}
.qb-hint{font-size:0.65rem;color:var(--text-3);}
.run-btn{display:flex;align-items:center;gap:5px;padding:0.48rem 1.1rem;background:var(--accent);color:#fff;border:none;border-radius:8px;font-size:0.76rem;font-weight:600;cursor:pointer;font-family:var(--font-b);transition:all 0.14s;}
.run-btn:hover{background:#4a3fe0;box-shadow:0 3px 10px rgba(91,79,255,0.3);}
.run-btn:disabled{background:#b5b0e8;cursor:not-allowed;box-shadow:none;}

/* Loader */
.ldr{display:none;background:var(--card);border:1px solid var(--card-border);border-radius:var(--r);padding:0.9rem 1rem;box-shadow:var(--sh);}
.ldr-steps{display:flex;gap:0.4rem;flex-wrap:wrap;margin-bottom:0.6rem;}
.ls{display:flex;align-items:center;gap:4px;font-size:0.67rem;padding:0.18rem 0.55rem;border-radius:5px;border:1px solid var(--card-border);color:var(--text-3);background:var(--bg);transition:all 0.3s;}
.ls.done{background:var(--green-dim);border-color:#00c89635;color:var(--green);}
.ls.act{background:var(--accent-dim);border-color:#5b4fff35;color:var(--accent);}
.ls .d{width:5px;height:5px;border-radius:50%;background:currentColor;}
.ls.act .d{animation:p 0.8s ease-in-out infinite;}
@keyframes p{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.4;transform:scale(0.75)}}
.ldr-prog{height:2px;background:var(--card-border);border-radius:2px;overflow:hidden;}
.ldr-fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--green));border-radius:2px;transition:width 0.4s ease;}

/* Result */
.rp{display:none;background:var(--card);border:1px solid var(--card-border);border-radius:var(--r);box-shadow:var(--sh);overflow:hidden;}
.rp-h{padding:0.8rem 1rem;border-bottom:1px solid var(--card-border);display:flex;align-items:center;justify-content:space-between;background:#fafaff;}
.rp-ht{font-family:var(--font-h);font-size:0.8rem;font-weight:600;}
.rp-m{display:flex;gap:0.35rem;}
.rch{font-size:0.65rem;font-weight:600;padding:0.18rem 0.55rem;border-radius:5px;}
.rch.g{background:var(--green-dim);color:var(--green);border:1px solid #00c89628;}
.rch.a{background:var(--accent-dim);color:var(--accent);border:1px solid #5b4fff28;}
.rp-b{padding:1rem;}
.rp-ans{font-size:0.8rem;line-height:1.88;color:var(--text);white-space:pre-wrap;max-height:400px;overflow-y:auto;padding-right:4px;}
.rp-ans::-webkit-scrollbar{width:3px;}
.rp-ans::-webkit-scrollbar-thumb{background:var(--card-border);border-radius:3px;}
.rp-src{margin-top:0.8rem;padding-top:0.8rem;border-top:1px solid var(--card-border);}
.rp-sl{font-size:0.62rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--text-3);margin-bottom:0.4rem;}
.stags{display:flex;flex-wrap:wrap;gap:0.3rem;}
.stag{font-size:0.65rem;padding:0.15rem 0.5rem;border-radius:4px;background:var(--green-dim);border:1px solid #00c89628;color:var(--green);font-weight:500;}

/* Page cards */
.pc{background:var(--card);border:1px solid var(--card-border);border-radius:var(--r);padding:1.1rem;box-shadow:var(--sh);}
.pt{font-family:var(--font-h);font-size:0.95rem;font-weight:700;margin-bottom:0.2rem;}
.ps{font-size:0.75rem;color:var(--text-2);margin-bottom:0.9rem;}
.le{padding:0.65rem;border:1px solid var(--card-border);border-radius:7px;margin-bottom:0.4rem;background:var(--bg);}
.lq{font-size:0.78rem;font-weight:500;margin-bottom:0.3rem;}
.lm{font-size:0.65rem;color:var(--text-3);display:flex;gap:0.65rem;}
.em{display:flex;align-items:center;justify-content:space-between;padding:0.6rem 0;border-bottom:1px solid var(--card-border);}
.em:last-child{border-bottom:none;}
.en{font-size:0.78rem;font-weight:500;}
.ev{font-family:var(--font-h);font-size:0.88rem;font-weight:700;color:var(--accent);}
.ebw{height:3px;background:var(--card-border);border-radius:2px;margin-top:3px;width:100px;}
.eb{height:100%;border-radius:2px;background:linear-gradient(90deg,var(--accent),var(--green));}
.sr2{padding:0.65rem;border:1px solid var(--card-border);border-radius:7px;margin-bottom:0.4rem;cursor:pointer;transition:all 0.14s;}
.sr2:hover{border-color:var(--accent);background:var(--accent-dim);}
.sr-tk{font-family:var(--font-h);font-size:0.7rem;font-weight:700;color:var(--accent);margin-bottom:2px;}
.sr-tx{font-size:0.73rem;color:var(--text-2);line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.sr-mt{font-size:0.62rem;color:var(--text-3);margin-top:3px;}

.err{display:none;background:#fff1f1;border:1px solid #fecaca;border-radius:7px;padding:0.65rem;font-size:0.75rem;color:#b91c1c;margin-top:0.4rem;}

select{padding:0.36rem 0.65rem;border:1px solid var(--card-border);border-radius:6px;font-family:var(--font-b);font-size:0.75rem;background:var(--bg);color:var(--text);outline:none;}
</style>
</head>
<body>

<aside class="sidebar">
  <div class="sidebar-logo">
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect width="18" height="18" rx="5" fill="#5b4fff"/><path d="M3 13l3.5-4.5 2.5 2.5L13 5" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
    <span>fin<span class="logo-dot">.</span>agent</span>
  </div>
  <div class="sidebar-user">
    <div class="avatar">FA</div>
    <div><div class="u-name">Finance AI</div><div class="u-role">Intelligence Agent</div></div>
  </div>
  <div class="nav-sec">
    <div class="nav-lbl">Analysis</div>
    <a class="nl on" onclick="sv('reports')" href="#">
      <svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>
      Company Reports
    </a>
    <a class="nl" onclick="sv('trends')" href="#">
      <svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
      Stock Trends
    </a>
    <a class="nl" onclick="sv('risks')" href="#">
      <svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      Risk Factors
    </a>
    <a class="nl" onclick="sv('log')" href="#">
      <svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/></svg>
      Query Log
    </a>
  </div>
  <div class="nav-sec">
    <div class="nav-lbl">Tools</div>
    <a class="nl" onclick="sv('search')" href="#">
      <svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      Search Filings
    </a>
    <a class="nl" onclick="sv('eval')" href="#">
      <svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
      Evaluation
    </a>
  </div>
  <div class="sidebar-foot">
    <a class="nl" href="/docs" target="_blank">
      <svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
      API Docs
    </a>
  </div>
</aside>

<div class="main">
  <header class="topbar">
    <div class="tb-title" id="tb-title">Company Intelligence Reports</div>
    <div class="tb-right">
      <span class="live-pill">LIVE</span>
      <button class="tb-btn" onclick="sv('log')">
        <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/></svg>
        Query Log
      </button>
    </div>
  </header>

  <div class="body-wrap">
    <!-- LEFT: company list -->
    <div class="p-left">
      <div class="fbar">
        <div class="sw">
          <svg width="12" height="12" fill="none" stroke="#9896a8" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" id="co-s" placeholder="Search companies..." oninput="rc()">
        </div>
        <div class="fp on" data-f="all" onclick="sf(this)">All</div>
        <div class="fp" data-f="Tech" onclick="sf(this)">Tech</div>
        <div class="fp" data-f="Finance" onclick="sf(this)">Finance</div>
        <div class="fp" data-f="Energy" onclick="sf(this)">Energy</div>
      </div>
      <div class="sr">
        <div class="sr-ct" id="co-ct"><strong>20</strong> companies</div>
        <div class="srt">Recommended ▾</div>
      </div>
      <div class="clist" id="clist"></div>
    </div>

    <!-- RIGHT: views -->
    <div class="p-right">

      <!-- Reports -->
      <div class="view on" id="view-reports">
        <div class="dh">
          <div class="dh-top">
            <div class="dh-logo">
              <img id="dh-img" src="" alt="" onerror="this.style.display='none';document.getElementById('dh-txt').style.display='flex'">
              <span id="dh-txt" style="display:none;font-family:var(--font-h);font-weight:700;font-size:0.8rem;color:var(--accent)"></span>
            </div>
            <div class="dh-inf">
              <div class="dh-name" id="dh-name">Apple Inc.</div>
              <div class="dh-sec" id="dh-sec">Technology / Consumer Electronics</div>
              <div class="dh-bgs">
                <span class="tag g" id="dh-b1">NASDAQ</span>
                <span class="tag a" id="dh-b2">FY2021-23</span>
                <span class="tag">SEC 10-K</span>
              </div>
            </div>
            <div class="dh-sc">
              <div class="dh-ring">
                <svg width="52" height="52" viewBox="0 0 52 52">
                  <circle cx="26" cy="26" r="22" fill="none" stroke="#e4e0d6" stroke-width="2.5"/>
                  <circle id="dh-arc" cx="26" cy="26" r="22" fill="none" stroke="#00c896" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="138.2" stroke-dashoffset="16.6"/>
                </svg>
                <div class="dh-sn" id="dh-sn">92</div>
              </div>
              <div class="dh-sl">Strong match</div>
            </div>
          </div>
          <div class="dh-acts">
            <button class="btn btn-p" onclick="sq('Analyze revenue trends for '+ct+' from 2021 to 2023')">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              Analyze
            </button>
            <button class="btn btn-s" onclick="sq('What are the main risk factors for '+ct+'?')">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
              Risk Report
            </button>
            <button class="btn btn-o" onclick="sq('Compare '+ct+' performance with sector peers in 2023')">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
              Compare
            </button>
          </div>
        </div>

        <div class="sg">
          <div class="sc"><div class="sc-lbl">Sections</div><div class="sc-val">4</div><div class="sc-sub">Revenue · Risk · MD&A · Overview</div></div>
          <div class="sc"><div class="sc-lbl">Fiscal Years</div><div class="sc-val">3</div><div class="sc-sub">2021 · 2022 · 2023</div></div>
          <div class="sc"><div class="sc-lbl">Index</div><div class="sc-val">100K+</div><div class="sc-sub">Document chunks</div></div>
        </div>

        <div class="qb">
          <div class="qb-h">
            <div class="qb-sp"><svg width="9" height="9" fill="#fff" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></div>
            Ask the Intelligence Agent
          </div>
          <div class="chips" id="qchips">
            <span class="chip" onclick="uc(this)">Revenue trends 2021–2023</span>
            <span class="chip" onclick="uc(this)">Key risk factors</span>
            <span class="chip" onclick="uc(this)">Stock volatility</span>
            <span class="chip" onclick="uc(this)">Compare with peers</span>
            <span class="chip" onclick="uc(this)">MD&A summary</span>
            <span class="chip" onclick="uc(this)">Cybersecurity risks</span>
          </div>
          <textarea class="qta" id="qi" rows="3" placeholder="e.g. Compare AAPL and MSFT risk factors for 2022 and 2023…"></textarea>
          <div class="qb-ft">
            <span class="qb-hint">Ctrl+Enter to run</span>
            <button class="run-btn" id="rbtn" onclick="rq()">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              Run Analysis
            </button>
          </div>
          <div class="err" id="err"></div>
        </div>

        <div class="ldr" id="ldr">
          <div class="ldr-steps" id="lsteps"></div>
          <div class="ldr-prog"><div class="ldr-fill" id="lfill" style="width:0%"></div></div>
        </div>

        <div class="rp" id="rp">
          <div class="rp-h">
            <div class="rp-ht" id="rp-t">Analysis Result</div>
            <div class="rp-m">
              <span class="rch g" id="rq-q"></span>
              <span class="rch a" id="rq-d"></span>
            </div>
          </div>
          <div class="rp-b">
            <div class="rp-ans" id="rp-ans"></div>
            <div class="rp-src">
              <div class="rp-sl">Sources retrieved</div>
              <div class="stags" id="rp-srcs"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Stock Trends -->
      <div class="view" id="view-trends">
        <div class="pc">
          <div class="pt">Stock Price Trends</div>
          <div class="ps">Historical OHLCV data · 2021–2023</div>
          <div style="display:flex;gap:0.5rem;margin-bottom:0.85rem;align-items:center;flex-wrap:wrap">
            <select id="tr-tk" onchange="lt()">
              <option>AAPL</option><option>MSFT</option><option>GOOGL</option><option>NVDA</option>
              <option>META</option><option>AMZN</option><option>TSLA</option><option>JPM</option>
              <option>BAC</option><option>JNJ</option><option>XOM</option><option>CVX</option>
            </select>
            <div style="display:flex;gap:0.3rem">
              <span class="fp on" style="font-size:0.68rem;padding:0.28rem 0.6rem" onclick="scr('ALL',this)">All</span>
              <span class="fp" style="font-size:0.68rem;padding:0.28rem 0.6rem" onclick="scr('2Y',this)">2Y</span>
              <span class="fp" style="font-size:0.68rem;padding:0.28rem 0.6rem" onclick="scr('1Y',this)">1Y</span>
            </div>
          </div>
          <div id="tr-stats" style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;margin-bottom:0.85rem"></div>
          <div style="position:relative">
            <canvas id="pc" height="180"></canvas>
            <div id="tr-empty" style="text-align:center;padding:1.5rem;color:var(--text-3);font-size:0.78rem">Loading…</div>
          </div>
        </div>
      </div>

      <!-- Risk Factors -->
      <div class="view" id="view-risks">
        <div class="pc">
          <div class="pt">Risk Factor Analysis</div>
          <div class="ps">Cross-company risk intelligence from SEC 10-K filings</div>
          <div class="chips" style="margin-bottom:0.75rem">
            <span class="chip" onclick="rsk('cybersecurity and data privacy risks across all companies')">Cybersecurity</span>
            <span class="chip" onclick="rsk('regulatory and compliance risks across companies')">Regulatory</span>
            <span class="chip" onclick="rsk('supply chain and operational risks')">Supply Chain</span>
            <span class="chip" onclick="rsk('macroeconomic inflation and interest rate risks')">Macro / Inflation</span>
            <span class="chip" onclick="rsk('geopolitical risks in energy and tech sectors')">Geopolitical</span>
            <span class="chip" onclick="rsk('talent acquisition and workforce risks')">Talent / HR</span>
          </div>
          <textarea class="qta" id="ri" placeholder="Ask about any risk factor across all company filings…" rows="2"></textarea>
          <button class="run-btn" style="margin-top:0.5rem;width:100%;justify-content:center" onclick="rsk(document.getElementById('ri').value)">
            <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            Analyze Risks
          </button>
          <div id="rsk-ldr" style="display:none;text-align:center;padding:0.85rem;font-size:0.75rem;color:var(--text-3)">Analyzing…</div>
          <div id="rsk-res" style="display:none;margin-top:0.75rem">
            <div id="rsk-ans" style="font-size:0.78rem;line-height:1.85;white-space:pre-wrap;max-height:340px;overflow-y:auto;padding:0.75rem;background:var(--bg);border-radius:8px;border:1px solid var(--card-border)"></div>
          </div>
        </div>
      </div>

      <!-- Query Log -->
      <div class="view" id="view-log">
        <div class="pc">
          <div class="pt">Query Log</div>
          <div class="ps">All agent runs with quality scores and source counts</div>
          <div id="log-list"><div style="text-align:center;padding:1.5rem;color:var(--text-3);font-size:0.78rem">No queries yet.</div></div>
        </div>
      </div>

      <!-- Search Filings -->
      <div class="view" id="view-search">
        <div class="pc">
          <div class="pt">Search Filings</div>
          <div class="ps">Hybrid BM25 + vector search across 100K+ document chunks</div>
          <div class="sw" style="margin-bottom:0.6rem">
            <svg width="12" height="12" fill="none" stroke="#9896a8" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" id="fs-q" placeholder="Search filings…" style="font-size:0.78rem">
          </div>
          <div style="display:flex;gap:0.5rem;margin-bottom:0.75rem;flex-wrap:wrap;align-items:center">
            <select id="fs-tk"><option value="">All companies</option><option>AAPL</option><option>MSFT</option><option>GOOGL</option><option>NVDA</option><option>META</option><option>AMZN</option><option>TSLA</option><option>JPM</option></select>
            <select id="fs-sc"><option value="">All sections</option><option value="risk_factors">Risk Factors</option><option value="revenue">Revenue</option><option value="business_overview">Business Overview</option><option value="md_and_a">MD&A</option></select>
            <button class="run-btn" style="padding:0.36rem 0.85rem;font-size:0.72rem" onclick="sf2()">Search</button>
          </div>
          <div id="sr-res"><div style="text-align:center;padding:1.25rem;color:var(--text-3);font-size:0.78rem">Enter a query to search</div></div>
        </div>
      </div>

      <!-- Evaluation -->
      <div class="view" id="view-eval">
        <div class="pc">
          <div class="pt">Evaluation Report</div>
          <div class="ps">Recall@K · Precision@K · Answer quality metrics</div>
          <div id="ev-con">
            <div style="text-align:center;padding:1.25rem">
              <button class="run-btn" onclick="le()">
                <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Run Evaluation Suite
              </button>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
const COS = [
  {t:"AAPL",name:"Apple Inc.",sec:"Technology / Consumer Electronics",type:"Tech",score:92,logo:"https://logo.clearbit.com/apple.com",exch:"NASDAQ"},
  {t:"MSFT",name:"Microsoft Corp.",sec:"Technology / Cloud",type:"Tech",score:91,logo:"https://logo.clearbit.com/microsoft.com",exch:"NASDAQ"},
  {t:"GOOGL",name:"Alphabet Inc.",sec:"Technology / Advertising",type:"Tech",score:89,logo:"https://logo.clearbit.com/google.com",exch:"NASDAQ"},
  {t:"NVDA",name:"NVIDIA Corp.",sec:"Semiconductors / AI",type:"Tech",score:95,logo:"https://logo.clearbit.com/nvidia.com",exch:"NASDAQ"},
  {t:"META",name:"Meta Platforms",sec:"Technology / Social Media",type:"Tech",score:87,logo:"https://logo.clearbit.com/meta.com",exch:"NASDAQ"},
  {t:"AMZN",name:"Amazon.com Inc.",sec:"E-Commerce / Cloud",type:"Tech",score:90,logo:"https://logo.clearbit.com/amazon.com",exch:"NASDAQ"},
  {t:"TSLA",name:"Tesla Inc.",sec:"Automotive / EV",type:"Tech",score:86,logo:"https://logo.clearbit.com/tesla.com",exch:"NASDAQ"},
  {t:"JPM",name:"JPMorgan Chase",sec:"Financial Services",type:"Finance",score:88,logo:"https://logo.clearbit.com/jpmorganchase.com",exch:"NYSE"},
  {t:"BAC",name:"Bank of America",sec:"Financial Services",type:"Finance",score:85,logo:"https://logo.clearbit.com/bankofamerica.com",exch:"NYSE"},
  {t:"JNJ",name:"Johnson & Johnson",sec:"Healthcare / Pharma",type:"Finance",score:84,logo:"https://logo.clearbit.com/jnj.com",exch:"NYSE"},
  {t:"XOM",name:"ExxonMobil Corp.",sec:"Energy / Oil & Gas",type:"Energy",score:83,logo:"https://logo.clearbit.com/exxonmobil.com",exch:"NYSE"},
  {t:"CVX",name:"Chevron Corp.",sec:"Energy / Oil & Gas",type:"Energy",score:82,logo:"https://logo.clearbit.com/chevron.com",exch:"NYSE"},
  {t:"WMT",name:"Walmart Inc.",sec:"Retail / Consumer Staples",type:"Finance",score:80,logo:"https://logo.clearbit.com/walmart.com",exch:"NYSE"},
  {t:"PG",name:"Procter & Gamble",sec:"Consumer Goods",type:"Finance",score:79,logo:"https://logo.clearbit.com/pg.com",exch:"NYSE"},
  {t:"HD",name:"Home Depot",sec:"Retail / Home Improvement",type:"Finance",score:81,logo:"https://logo.clearbit.com/homedepot.com",exch:"NYSE"},
  {t:"ABBV",name:"AbbVie Inc.",sec:"Pharmaceuticals",type:"Finance",score:78,logo:"https://logo.clearbit.com/abbvie.com",exch:"NYSE"},
  {t:"PFE",name:"Pfizer Inc.",sec:"Pharmaceuticals",type:"Finance",score:77,logo:"https://logo.clearbit.com/pfizer.com",exch:"NYSE"},
  {t:"LLY",name:"Eli Lilly",sec:"Pharmaceuticals",type:"Finance",score:83,logo:"https://logo.clearbit.com/lilly.com",exch:"NYSE"},
  {t:"KO",name:"Coca-Cola Co.",sec:"Consumer Beverages",type:"Finance",score:76,logo:"https://logo.clearbit.com/coca-cola.com",exch:"NYSE"},
  {t:"PEP",name:"PepsiCo Inc.",sec:"Consumer Beverages",type:"Finance",score:77,logo:"https://logo.clearbit.com/pepsico.com",exch:"NYSE"},
];
const CHIPS = {
  "Revenue trends 2021–2023":()=>`Analyze revenue trends for ${ct} from 2021 to 2023`,
  "Key risk factors":()=>`What are the main risk factors for ${ct} in their SEC 10-K filing?`,
  "Stock volatility":()=>`Analyze stock price volatility for ${ct} between 2021 and 2023`,
  "Compare with peers":()=>`Compare ${ct} revenue and risk factors with its sector peers`,
  "MD&A summary":()=>`Summarize the MD&A section for ${ct} for fiscal year 2023`,
  "Cybersecurity risks":()=>`What cybersecurity risks does ${ct} highlight in their filings?`,
};
const VTITLES = {reports:"Company Intelligence Reports",trends:"Stock Price Trends",risks:"Risk Factor Analysis",log:"Query Log",search:"Search Filings",eval:"Evaluation Suite"};
const STEPS = ["Planning","Retrieving","Re-ranking","Analyzing","Critiquing"];

let ci = 0, ct = "AAPL", af = "all", log = [], pChart = null, apd = {}, cr = "ALL";

function rc() {
  const q = document.getElementById('co-s').value.toLowerCase();
  const el = document.getElementById('clist'); el.innerHTML = '';
  let n = 0;
  COS.forEach((c,i) => {
    const ms = !q||c.t.toLowerCase().includes(q)||c.name.toLowerCase().includes(q)||c.sec.toLowerCase().includes(q);
    const mf = af==='all'||c.type===af;
    if(!ms||!mf) return; n++;
    const d = document.createElement('div');
    d.className='cc'+(i===ci?' sel':'');
    d.onclick=()=>sel(i);
    d.innerHTML=`<div class="cc-top">
      <div class="co-logo"><img src="${c.logo}" alt="${c.t}" onerror="this.style.display='none';this.nextSibling.style.display='flex'"><span style="display:none;font-family:var(--font-h);font-weight:700;font-size:0.7rem;color:var(--accent)">${c.t[0]}</span></div>
      <div class="ci"><div class="ci-name">${c.name}</div><div class="ci-sub">${c.t} · ${c.sec}</div></div>
      <div class="ring"><svg width="38" height="38" viewBox="0 0 38 38"><circle cx="19" cy="19" r="15" fill="none" stroke="#e4e0d6" stroke-width="2.2"/><circle cx="19" cy="19" r="15" fill="none" stroke="#00c896" stroke-width="2.2" stroke-linecap="round" stroke-dasharray="94.2" stroke-dashoffset="${94.2*(1-c.score/100)}"/></svg><div class="ring-num">${c.score}</div></div>
    </div>
    <div class="ct"><span class="tag g">${c.exch}</span><span class="tag a">FY2021-23</span><span class="tag">10-K</span></div>
    <div class="cf"><span class="cf-t">Updated today</span><button class="bm" onclick="event.stopPropagation()"><svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg></button></div>`;
    el.appendChild(d);
  });
  document.getElementById('co-ct').innerHTML=`<strong>${n}</strong> companies`;
}

function sf(el){document.querySelectorAll('.fp').forEach(p=>p.classList.remove('on'));el.classList.add('on');af=el.dataset.f;rc();}

function sel(i){
  ci=i; const c=COS[i]; ct=c.t;
  const img=document.getElementById('dh-img'),txt=document.getElementById('dh-txt');
  img.src=c.logo; img.style.display=''; txt.style.display='none'; txt.textContent=c.t[0];
  document.getElementById('dh-name').textContent=c.name;
  document.getElementById('dh-sec').textContent=c.sec;
  document.getElementById('dh-b1').textContent=c.exch;
  document.getElementById('dh-sn').textContent=c.score;
  document.getElementById('dh-arc').setAttribute('stroke-dashoffset',138.2*(1-c.score/100));
  document.getElementById('rp').style.display='none';
  document.getElementById('err').style.display='none';
  rc(); sv('reports');
}

function sv(id){
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('on'));
  document.querySelectorAll('.nl').forEach(l=>l.classList.remove('on'));
  document.getElementById('view-'+id).classList.add('on');
  document.querySelectorAll('.nl').forEach(l=>{if(l.getAttribute('onclick')&&l.getAttribute('onclick').includes("'"+id+"'"))l.classList.add('on');});
  document.getElementById('tb-title').textContent=VTITLES[id]||'';
  if(id==='trends'){document.getElementById('tr-tk').value=ct;lt();}
  if(id==='log') rl();
}

function sq(q){document.getElementById('qi').value=q;document.getElementById('qi').focus();sv('reports');}
function uc(el){const fn=CHIPS[el.textContent];if(fn)document.getElementById('qi').value=fn();}

async function rq(){
  const q=document.getElementById('qi').value.trim(); if(!q) return;
  document.getElementById('rbtn').disabled=true;
  document.getElementById('rp').style.display='none';
  document.getElementById('err').style.display='none';
  const ldr=document.getElementById('ldr'); ldr.style.display='block';
  const se=document.getElementById('lsteps');
  se.innerHTML=STEPS.map(s=>`<div class="ls" id="ls-${s}"><div class="d"></div>${s}</div>`).join('');
  let si=0;
  function ast(i){STEPS.forEach((s,j)=>{const e=document.getElementById('ls-'+s);e.classList.toggle('done',j<i);e.classList.toggle('act',j===i);});document.getElementById('lfill').style.width=Math.round((i+1)/STEPS.length*90)+'%';}
  const st=setInterval(()=>{if(si<STEPS.length)ast(si++);},1100);
  try{
    const res=await fetch('/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q})});
    if(!res.ok) throw new Error(await res.text());
    const data=await res.json();
    clearInterval(st); STEPS.forEach(s=>document.getElementById('ls-'+s).className='ls done');
    document.getElementById('lfill').style.width='100%';
    setTimeout(()=>{ldr.style.display='none';},350);
    document.getElementById('rp-t').textContent='Analysis — '+(q.length>55?q.slice(0,55)+'…':q);
    document.getElementById('rq-q').textContent='Quality '+(data.quality_score*100).toFixed(0)+'%';
    document.getElementById('rq-d').textContent=data.doc_count+' docs';
    if (data.blocked) {
        document.getElementById('rp-t').textContent = 'Query Blocked';
        document.getElementById('rp-ans').style.color = 'var(--red)';
    } else {
        document.getElementById('rp-t').textContent = 'Analysis — '+(q.length>55?q.slice(0,55)+'...':q);
        document.getElementById('rp-ans').style.color = 'var(--text)';
    }
    document.getElementById('rp-ans').textContent = data.answer;
    const se2=document.getElementById('rp-srcs'); se2.innerHTML='';
    (data.sources||[]).forEach(s=>{const t=document.createElement('span');t.className='stag';t.textContent=s;se2.appendChild(t);});
    document.getElementById('rp').style.display='block';
    log.unshift({query:q,quality:data.quality_score,docs:data.doc_count,time:new Date().toLocaleTimeString(),ticker:ct});
  }catch(e){
    clearInterval(st);ldr.style.display='none';
    const eb=document.getElementById('err');eb.style.display='block';eb.textContent='Error: '+e.message;
  }finally{document.getElementById('rbtn').disabled=false;}
}

async function rsk(q){
  if(!q||!q.trim()) return;
  document.getElementById('rsk-ldr').style.display='block';
  document.getElementById('rsk-res').style.display='none';
  try{
    const res=await fetch('/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q})});
    const data=await res.json();
    document.getElementById('rsk-ans').textContent=data.answer;
    document.getElementById('rsk-res').style.display='block';
    log.unshift({query:q,quality:data.quality_score,docs:data.doc_count,time:new Date().toLocaleTimeString(),ticker:'ALL'});
  }catch(e){alert('Error: '+e.message);}
  finally{document.getElementById('rsk-ldr').style.display='none';}
}

function rl(){
  const el=document.getElementById('log-list');
  if(!log.length){el.innerHTML='<div style="text-align:center;padding:1.5rem;color:var(--text-3);font-size:0.78rem">No queries yet.</div>';return;}
  el.innerHTML=log.map((l,i)=>`<div class="le"><div class="lq">${i+1}. ${l.query}</div><div class="lm"><span>${l.ticker}</span><span>Quality: <strong style="color:var(--green)">${(l.quality*100).toFixed(0)}%</strong></span><span>${l.docs} docs</span><span>${l.time}</span></div></div>`).join('');
}

async function sf2(){
  const q=document.getElementById('fs-q').value.trim(); if(!q) return;
  const tk=document.getElementById('fs-tk').value, sc=document.getElementById('fs-sc').value;
  document.getElementById('sr-res').innerHTML='<div style="text-align:center;padding:1rem;color:var(--text-3);font-size:0.75rem">Searching…</div>';
  try{
    const res=await fetch('/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q,ticker:tk,section:sc})});
    const data=await res.json();
    if(!data.results||!data.results.length){document.getElementById('sr-res').innerHTML='<div style="text-align:center;padding:1rem;color:var(--text-3)">No results.</div>';return;}
    document.getElementById('sr-res').innerHTML=data.results.map(r=>`<div class="sr2"><div class="sr-tk">${r.ticker} · ${r.section} · FY${r.year}</div><div class="sr-tx">${r.text}</div><div class="sr-mt">Score: ${r.score.toFixed(3)}</div></div>`).join('');
  }catch(e){document.getElementById('sr-res').innerHTML=`<div style="color:var(--red);font-size:0.75rem">Error: ${e.message}</div>`;}
}

async function lt(){
  const tk=document.getElementById('tr-tk').value; ct=tk;
  document.getElementById('tr-empty').style.display='block';
  document.getElementById('tr-empty').textContent='Loading…';
  try{
    const res=await fetch('/prices/'+tk); const data=await res.json();
    if(!data.dates||!data.dates.length) throw new Error('No data');
    apd=data; rch2(data);
    document.getElementById('tr-empty').style.display='none';
    const cl=data.closes,f=cl[0],l=cl[cl.length-1],chg=((l-f)/f*100).toFixed(1);
    document.getElementById('tr-stats').innerHTML=`
      <div class="sc"><div class="sc-lbl">Latest</div><div class="sc-val">$${l.toFixed(2)}</div></div>
      <div class="sc"><div class="sc-lbl">Change</div><div class="sc-val" style="color:${chg>=0?'var(--green)':'var(--red)'}">${chg>=0?'+':''}${chg}%</div></div>
      <div class="sc"><div class="sc-lbl">High</div><div class="sc-val">$${Math.max(...cl).toFixed(2)}</div></div>
      <div class="sc"><div class="sc-lbl">Low</div><div class="sc-val">$${Math.min(...cl).toFixed(2)}</div></div>`;
  }catch(e){document.getElementById('tr-empty').textContent='No price data for '+tk;}
}

function scr(r,el){document.querySelectorAll('#view-trends .fp').forEach(t=>t.classList.remove('on'));el.classList.add('on');cr=r;if(apd.dates)rch2(apd);}

function rch2(data){
  let ds=data.dates,cl=data.closes;
  if(cr==='1Y'){ds=ds.slice(-252);cl=cl.slice(-252);}
  else if(cr==='2Y'){ds=ds.slice(-504);cl=cl.slice(-504);}
  const ctx=document.getElementById('pc').getContext('2d');
  if(pChart)pChart.destroy();
  pChart=new Chart(ctx,{type:'line',data:{labels:ds,datasets:[{data:cl,borderColor:'#5b4fff',borderWidth:1.5,backgroundColor:'rgba(91,79,255,0.05)',fill:true,tension:0.3,pointRadius:0}]},options:{responsive:true,interaction:{mode:'index',intersect:false},plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>'$'+c.parsed.y.toFixed(2)}}},scales:{x:{grid:{display:false},ticks:{maxTicksLimit:7,font:{size:10},color:'#9896a8'}},y:{grid:{color:'#e4e0d618'},ticks:{font:{size:10},color:'#9896a8',callback:v=>'$'+v.toFixed(0)}}}}});
}

async function le(){
  document.getElementById('ev-con').innerHTML='<div style="text-align:center;padding:1rem;color:var(--text-3);font-size:0.75rem">Running evaluation…</div>';
  try{
    const res=await fetch('/evaluate'); const data=await res.json();
    document.getElementById('ev-con').innerHTML=`
      <div style="margin-bottom:0.85rem">
        <div class="em"><div><div class="en">Average Recall@10</div><div class="ebw"><div class="eb" style="width:${(data.avg_recall_at_10*100).toFixed(0)}%"></div></div></div><div class="ev">${(data.avg_recall_at_10*100).toFixed(1)}%</div></div>
        <div class="em"><div><div class="en">Average Precision@10</div><div class="ebw"><div class="eb" style="width:${(data.avg_precision_at_10*100).toFixed(0)}%"></div></div></div><div class="ev">${(data.avg_precision_at_10*100).toFixed(1)}%</div></div>
      </div>
      <div style="font-size:0.62rem;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">Per-query results</div>
      ${(data.per_query||[]).map(q=>`<div class="le"><div class="lq">${q.query}</div><div class="lm"><span>Recall@10: <strong style="color:var(--green)">${(q['recall@10']*100).toFixed(0)}%</strong></span><span>Precision@10: <strong style="color:var(--accent)">${(q['precision@10']*100).toFixed(0)}%</strong></span></div></div>`).join('')}`;
  }catch(e){document.getElementById('ev-con').innerHTML=`<div style="color:var(--red);font-size:0.75rem;padding:0.75rem">Run: python -m src.evaluation.eval first, then retry.</div>`;}
}

document.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('qi').addEventListener('keydown',e=>{if(e.key==='Enter'&&e.ctrlKey)rq();});
  document.getElementById('ri').addEventListener('keydown',e=>{if(e.key==='Enter'&&e.ctrlKey)rsk(e.target.value);});
  document.getElementById('fs-q').addEventListener('keydown',e=>{if(e.key==='Enter')sf2();});
  rc(); sel(0);
});
</script>
</body>
</html>"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    orchestrator = FinancialAgentOrchestrator()
    orchestrator.build_index()
    yield


app = FastAPI(
    title="Financial Intelligence Agent",
    description="Multi-agent RAG system — 100K+ financial document chunks",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list
    quality_score: float
    doc_count: int
    blocked: bool = False


class SearchRequest(BaseModel):
    query: str
    ticker: str = ""
    section: str = ""


@app.get("/", response_class=HTMLResponse)
async def root():
    return UI_HTML


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    result = orchestrator.answer(req.query)
    return QueryResponse(
        query=result["query"],
        answer=result["answer"],
        sources=result.get("sources", []),
        quality_score=result.get("quality_score", 0.0),
        doc_count=result.get("doc_count", 0),
        blocked=result.get("blocked", False),
    )


@app.post("/search")
async def search_endpoint(req: SearchRequest):
    filters = {}
    if req.ticker:
        filters["ticker"] = [req.ticker]
    if req.section:
        filters["section"] = req.section
    docs = orchestrator.retriever.hybrid_search(req.query, k=10, filters=filters)
    results = [
        {
            "ticker": d["metadata"].get("ticker", ""),
            "section": d["metadata"].get("section", ""),
            "year": d["metadata"].get("fiscal_year", ""),
            "text": d["text"][:300],
            "score": d.get("rerank_score", d.get("score", 0)),
        }
        for d in docs
    ]
    return {"results": results}


@app.get("/prices/{ticker}")
async def prices_endpoint(ticker: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT date, close FROM stock_prices WHERE ticker=? ORDER BY date ASC",
            (ticker.upper(),),
        )
        rows = c.fetchall()
        conn.close()
        if not rows:
            return {"dates": [], "closes": []}
        return {
            "ticker": ticker,
            "dates": [r[0] for r in rows],
            "closes": [r[1] for r in rows],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/evaluate")
async def evaluate_endpoint():
    from pathlib import Path
    report = Path("evaluation/results/eval_report.json")
    if report.exists():
        return json.loads(report.read_text())
    try:
        from src.evaluation.eval import run_evaluation
        run_evaluation()
        if report.exists():
            return json.loads(report.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail="Run: python -m src.evaluation.eval")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}