#!/usr/bin/env python3
import os
import time
import argparse
from typing import Dict, Optional, List

import requests
import pandas as pd
from bs4 import BeautifulSoup
from jinja2 import Template

# 🎯 Full list of classes with their type IDs
CLASSES: Dict[str, int] = {
    'Warrior': 1,
    'Cleric': 2,
    'Paladin': 3,
    'Ranger': 4,
    'ShadowKnight': 5,
    'Druid': 6,
    'Monk': 7,
    'Bard': 8,
    'Rogue': 9,
    'Shaman': 10,
    'Necromancer': 11,
    'Wizard': 12,
    'Magician': 13,
    'Enchanter': 14,
    'Beastlord': 15,
    'Berserker': 16,
}

# Basic colour theme for each class used in the generated HTML. This is far from
# accurate to the game's palette but provides a quick way to differentiate the
# pages when rendered.
CLASS_COLORS: Dict[str, str] = {
    'Warrior': '#8e2d2d',
    'Cleric': '#ccccff',
    'Paladin': '#ffd700',
    'Ranger': '#228b22',
    'ShadowKnight': '#551a8b',
    'Druid': '#a0522d',
    'Monk': '#556b2f',
    'Bard': '#ff69b4',
    'Rogue': '#708090',
    'Shaman': '#20b2aa',
    'Necromancer': '#4b0082',
    'Wizard': '#1e90ff',
    'Magician': '#ff8c00',
    'Enchanter': '#9370db',
    'Beastlord': '#a52a2a',
    'Berserker': '#b22222',
}

BASE_URL = 'https://alla.clumsysworld.com/'
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>{{ cls }} Spells - Norrath Compendium</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500;600&family=Crimson+Text:wght@400;600&display=swap');
        
        :root {
            --primary-color: {{ color }};
            --primary-rgb: {{ color_rgb }};
            --bg-dark: #0a0e1a;
            --bg-darker: #050810;
            --card-bg: rgba(42, 46, 54, 0.95);
            --text-light: #e2e8f0;
            --text-dark: #f8fafc;
            --shadow-color: rgba(0, 0, 0, 0.4);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        html {
            background: var(--bg-darker);
            background-attachment: fixed;
        }
        
        body { 
            font-family: 'Inter', sans-serif;
            background: 
                var(--bg-darker),
                radial-gradient(circle at 20% 50%, rgba(var(--primary-rgb), 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(var(--primary-rgb), 0.2) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(var(--primary-rgb), 0.1) 0%, transparent 50%),
                linear-gradient(135deg, var(--bg-darker) 0%, var(--bg-dark) 100%);
            background-attachment: fixed;
            background-size: 100% 100%;
            min-height: 100vh;
            color: var(--text-light);
            position: relative;
            overflow-x: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                var(--bg-darker),
                url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="0.5" fill="rgba(255,255,255,0.03)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            pointer-events: none;
            z-index: 1;
            will-change: transform;
        }
        
        .main-container {
            position: relative;
            z-index: 2;
            padding: 40px 20px;
            max-width: 1400px;
            margin: 0 auto;
            background: transparent;
        }
        
        /* Scroll blur effect */
        .scroll-blur .spell-card {
            filter: blur(3px);
            opacity: 0.7;
            transform: scale(0.98);
        }
        
        .scroll-blur .level-section {
            filter: blur(3px);
            opacity: 0.7;
            transform: scale(0.98);
        }
        
        .scroll-blur .level-header {
            filter: blur(3px);
            opacity: 0.7;
            transform: scale(0.98);
        }
        
        .hero-section {
            text-align: center;
            margin-bottom: 60px;
            position: relative;
            background: transparent;
        }
        
        .hero-section::before {
            content: '';
            position: absolute;
            top: -50%;
            left: 50%;
            transform: translateX(-50%);
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(var(--primary-rgb), 0.4) 0%, transparent 70%);
            border-radius: 50%;
            filter: blur(60px);
            z-index: -1;
        }
        
        .home-button {
            position: absolute;
            top: 0;
            left: 0;
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.8));
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 20px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 4px 12px rgba(var(--primary-rgb), 0.3);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: 'Inter', sans-serif;
        }
        
        .home-button::before {
            content: '';
            width: 0;
            height: 0;
            border-top: 5px solid transparent;
            border-bottom: 5px solid transparent;
            border-right: 8px solid white;
            transition: all 0.3s ease;
        }
        
        .home-button:hover {
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.95), var(--primary-color));
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 8px 20px rgba(var(--primary-rgb), 0.4);
            text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
        }
        
        .home-button:hover::before {
            border-right-color: #e8f4fd;
            transform: translateX(-2px);
        }
        
        .home-button:active {
            transform: translateY(0) scale(1.02);
            box-shadow: 0 4px 12px rgba(var(--primary-rgb), 0.6);
        }
        
        .class-title {
            font-family: 'Cinzel', serif;
            font-size: 4.5em;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-color) 0%, rgba(255,255,255,0.8) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 15px;
            text-shadow: 0 0 30px rgba(var(--primary-rgb), 0.5);
            animation: glow 3s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 20px rgba(var(--primary-rgb), 0.5); }
            to { text-shadow: 0 0 40px rgba(var(--primary-rgb), 0.8), 0 0 60px rgba(var(--primary-rgb), 0.4); }
        }
        
        .class-subtitle {
            font-size: 1.4em;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 300;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        
        .stats-dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-bottom: 60px;
        }
        
        .stat-card {
            background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-rgb), 0.2), transparent);
            transition: left 0.6s;
        }
        
        .stat-card:hover::before {
            left: 100%;
        }
        
        .stat-card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 20px 40px rgba(var(--primary-rgb), 0.3);
        }
        
        .stat-number {
            font-size: 3.5em;
            font-weight: 700;
            color: var(--primary-color);
            display: block;
            margin-bottom: 10px;
            font-family: 'Cinzel', serif;
        }
        
        .stat-label {
            font-size: 1.1em;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: rgba(255,255,255,0.8);
            font-weight: 500;
        }
        
        .level-navigator {
            background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 60px;
            position: relative;
            overflow: hidden;
        }
        
        .level-navigator::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.05), transparent);
            pointer-events: none;
        }
        
        .level-nav-title {
            font-family: 'Cinzel', serif;
            font-size: 1.8em;
            font-weight: 600;
            color: var(--primary-color);
            text-align: center;
            margin-bottom: 25px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .level-matrix {
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            gap: 8px;
            max-width: 600px;
            margin: 0 auto;
            position: relative;
        }
        
        .level-cell {
            aspect-ratio: 1;
            background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
            color: rgba(255, 255, 255, 0.7);
            min-height: 40px;
            max-height: 40px;
            width: 100%;
            box-sizing: border-box;
            text-align: center;
            line-height: 1;
        }
        
        .level-cell.disabled {
            background: linear-gradient(135deg, rgba(100,100,100,0.15), rgba(80,80,80,0.08));
            border: 1px solid rgba(100,100,100,0.2);
            color: rgba(180, 180, 180, 0.6);
            cursor: not-allowed;
            opacity: 0.6;
            font-weight: 400;
        }
        
        .level-cell.disabled:hover {
            transform: none;
            background: linear-gradient(135deg, rgba(100,100,100,0.15), rgba(80,80,80,0.08));
            border-color: rgba(100,100,100,0.2);
            color: rgba(180, 180, 180, 0.6);
            box-shadow: none;
            text-shadow: none;
        }
        
        .level-cell.disabled::before {
            display: none;
        }
        
        .level-cell::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-rgb), 0.3), transparent);
            transition: left 0.4s ease;
        }
        
        .level-cell:hover::before {
            left: 100%;
        }
        
        .level-cell:hover {
            transform: translateY(-2px) scale(1.05);
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.3), rgba(var(--primary-rgb), 0.15));
            border-color: rgba(var(--primary-rgb), 0.6);
            color: white;
            box-shadow: 0 8px 20px rgba(var(--primary-rgb), 0.4);
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
        }
        
        .level-cell:active {
            transform: translateY(0) scale(1.02);
            box-shadow: 0 4px 10px rgba(var(--primary-rgb), 0.6);
        }
        
        .level-cell.available {
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.2), rgba(var(--primary-rgb), 0.1));
            border-color: rgba(var(--primary-rgb), 0.4);
            color: var(--text-light);
            font-weight: 700;
        }
        
        .level-cell.available:hover {
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.8));
            color: white;
            transform: translateY(-3px) scale(1.08);
            box-shadow: 0 12px 25px rgba(var(--primary-rgb), 0.5);
        }
        
        .level-section {
            margin-bottom: 80px;
            opacity: 0;
            animation: fadeInUp 0.8s ease-out forwards;
            scroll-margin-top: 100px;
        }
        
        .level-section:nth-child(even) { animation-delay: 0.2s; }
        .level-section:nth-child(odd) { animation-delay: 0.4s; }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .level-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.2), rgba(var(--primary-rgb), 0.05));
            backdrop-filter: blur(10px);
            border: 1px solid rgba(var(--primary-rgb), 0.3);
            border-radius: 15px;
            padding: 25px 35px;
            margin-bottom: 30px;
            position: relative;
        }
        
        .level-title {
            font-family: 'Cinzel', serif;
            font-size: 2.2em;
            font-weight: 600;
            color: var(--primary-color);
        }
        
        .level-header-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .level-count {
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: 700;
            font-size: 0.9em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .go-to-top-btn {
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.8));
            color: white;
            border: none;
            border-radius: 12px;
            padding: 10px 16px;
            font-size: 0.85em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 4px 12px rgba(var(--primary-rgb), 0.3);
            display: flex;
            align-items: center;
            gap: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: relative;
            overflow: hidden;
        }
        
        .go-to-top-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s ease;
        }
        
        .go-to-top-btn:hover::before {
            left: 100%;
        }
        
        .go-to-top-btn:hover {
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.95), var(--primary-color));
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 8px 20px rgba(var(--primary-rgb), 0.4);
            text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
        }
        
        .go-to-top-btn:active {
            transform: translateY(0) scale(1.02);
            box-shadow: 0 4px 12px rgba(var(--primary-rgb), 0.6);
        }
        
        /* CSS arrow pointing up */
        .go-to-top-btn::after {
            content: '';
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 6px solid white;
            transition: all 0.3s ease;
        }
        
        .go-to-top-btn:hover::after {
            border-bottom-color: #e8f4fd;
            transform: translateY(-1px);
        }
        
        .spells-masonry {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 25px;
            align-items: start;
        }
        
        .spell-card {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 0;
            box-shadow: 0 10px 30px var(--shadow-color);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
            border: 2px solid rgba(var(--primary-rgb), 0.4);
        }
        
        .spell-card:hover {
            transform: translateY(-8px) rotate(1deg);
            box-shadow: 0 25px 50px rgba(var(--primary-rgb), 0.4);
            border: 2px solid rgba(var(--primary-rgb), 0.7);
        }
        
        .spell-header {
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.8));
            color: white;
            padding: 20px 25px;
            position: relative;
        }
        
        .spell-icon {
            position: absolute;
            top: 10px;
            right: 15px;
            width: 48px;
            height: 48px;
            border-radius: 12px;
            border: 3px solid rgba(255,255,255,0.4);
            background: rgba(255,255,255,0.1);
            padding: 3px;
            transition: all 0.3s ease;
        }
        
        .spell-icon:hover {
            transform: scale(1.15);
            border-color: rgba(255,255,255,0.9);
            box-shadow: 0 0 20px rgba(255,255,255,0.5);
        }
        
        .spell-name {
            font-family: 'Cinzel', serif;
            font-size: 1.6em;
            font-weight: 600;
            margin-bottom: 5px;
            padding-right: 70px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            color: #ffffff;
        }
        
        .spell-level {
            font-size: 0.9em;
            opacity: 0.9;
            font-weight: 500;
        }
        
        .spell-body {
            padding: 25px;
            color: var(--text-dark);
            font-family: 'Crimson Text', serif;
        }
        
        .spell-attributes {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .spell-attribute {
            display: flex;
            flex-direction: column;
            background: rgba(var(--primary-rgb), 0.05);
            padding: 12px;
            border-radius: 10px;
            border-left: 3px solid var(--primary-color);
            position: relative;
            font-family: 'Crimson Text', serif;
        }
        
        .attribute-label {
            font-size: 0.85em;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: 'Inter', sans-serif;
        }
        
        .attribute-value {
            font-size: 1em;
            font-weight: 400;
            color: var(--text-dark);
            font-family: 'Crimson Text', serif;
        }
        
        /* Target type color coding */
        .target-self { background: rgba(255, 255, 0, 0.15) !important; border-left-color: #ffd700 !important; }
        .target-single { background: rgba(255, 0, 0, 0.15) !important; border-left-color: #ff4444 !important; }
        .target-aoe-target { background: rgba(0, 255, 0, 0.15) !important; border-left-color: #44ff44 !important; }
        .target-aoe-caster { background: rgba(0, 100, 255, 0.15) !important; border-left-color: #4488ff !important; }
        .target-group { background: rgba(150, 0, 255, 0.15) !important; border-left-color: #9944ff !important; }

        .spell-id-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .copy-btn {
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.8));
            color: white;
            border: none;
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 0.8em;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-left: 10px;
            box-shadow: 0 2px 8px rgba(var(--primary-rgb), 0.3);
            display: flex;
            align-items: center;
            gap: 4px;
            min-width: 32px;
            height: 28px;
            justify-content: center;
            position: relative;
        }
        
        .copy-btn:hover {
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.9), var(--primary-color));
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(var(--primary-rgb), 0.4);
        }
        
        .copy-btn:active {
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(var(--primary-rgb), 0.3);
        }
        
        /* CSS-based clipboard icon */
        .copy-btn::before {
            content: '';
            width: 12px;
            height: 14px;
            border: 2px solid white;
            border-radius: 2px;
            position: relative;
            background: transparent;
        }
        
        .copy-btn::after {
            content: '';
            position: absolute;
            width: 8px;
            height: 10px;
            border: 1.5px solid white;
            border-radius: 1px;
            background: rgba(255,255,255,0.2);
            top: 50%;
            left: 50%;
            transform: translate(-30%, -45%);
        }
        
        .copy-btn:hover::before {
            border-color: #e8f4fd;
        }
        
        .copy-btn:hover::after {
            border-color: #e8f4fd;
            background: rgba(232,244,253,0.3);
        }
        
        .copy-popup {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--primary-color);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        }
        
        .copy-popup.show {
            opacity: 1;
        }
        
        @media (max-width: 768px) {
            .class-title { font-size: 3em; }
            .stats-dashboard { grid-template-columns: 1fr; }
            .spells-masonry { grid-template-columns: 1fr; }
            .spell-attributes { grid-template-columns: 1fr; }
            .level-matrix { grid-template-columns: repeat(5, 1fr); }
            .level-navigator { padding: 20px; }
            .level-header { flex-direction: column; gap: 15px; text-align: center; }
            .level-header-right { flex-direction: row; justify-content: center; }
            .home-button { position: static; margin: 0 auto 20px auto; }
        }
        
        @media (max-width: 480px) {
            .level-matrix { grid-template-columns: repeat(5, 1fr); gap: 6px; }
            .level-cell { font-size: 0.8em; min-height: 35px; }
            .go-to-top-btn { padding: 8px 12px; font-size: 0.8em; }
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="hero-section">
            <a href="index.html" class="home-button">Home</a>
            <h1 class="class-title">{{ cls }}</h1>
            <p class="class-subtitle">Spell Compendium</p>
        </div>
        
        <div class="stats-dashboard">
            <div class="stat-card">
                <span class="stat-number">{{ total_spells }}</span>
                <span class="stat-label">Total Spells</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{ max_level }}</span>
                <span class="stat-label">Max Level</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{ schools_count }}</span>
                <span class="stat-label">Magic Schools</span>
            </div>
        </div>
        
        <div class="level-navigator">
            <h3 class="level-nav-title">Quick Level Navigation</h3>
            <div class="level-matrix" id="levelMatrix">
                <!-- Level cells will be populated by JavaScript -->
            </div>
        </div>
        
        {{ content|safe }}
    </div>
    
    <!-- Copy confirmation popup -->
    <div id="copyPopup" class="copy-popup">
        Spell ID copied to clipboard!
    </div>
    
    <script>
        let isScrolling = false;
        let scrollTimeout;
        
        // Initialize level navigation matrix
        function initializeLevelMatrix() {
            const matrix = document.getElementById('levelMatrix');
            const availableLevels = new Set();
            
            // Find all level sections on the page
            const levelSections = document.querySelectorAll('.level-section');
            levelSections.forEach(section => {
                const levelTitle = section.querySelector('.level-title');
                if (levelTitle) {
                    const levelMatch = levelTitle.textContent.match(/Level (\\d+)/);
                    if (levelMatch) {
                        availableLevels.add(parseInt(levelMatch[1]));
                    }
                }
            });
            
            // Create 60 level cells (10x6 grid)
            for (let i = 1; i <= 60; i++) {
                const cell = document.createElement('div');
                cell.className = 'level-cell';
                cell.textContent = String(i);
                cell.setAttribute('data-level', String(i));
                
                // Mark available levels
                if (availableLevels.has(i)) {
                    cell.classList.add('available');
                    cell.style.cursor = 'pointer';
                    cell.addEventListener('click', () => scrollToLevel(i));
                } else {
                    cell.classList.add('disabled');
                    cell.style.cursor = 'not-allowed';
                    cell.title = `No spells available at level ${i}`;
                }
                
                matrix.appendChild(cell);
            }
        }
        
        // Apply blur effect during scrolling
        function applyScrollBlur() {
            if (!isScrolling) {
                isScrolling = true;
                document.body.classList.add('scroll-blur');
            }
            
            // Clear existing timeout
            clearTimeout(scrollTimeout);
            
            // Remove blur after scrolling stops
            scrollTimeout = setTimeout(() => {
                isScrolling = false;
                document.body.classList.remove('scroll-blur');
            }, 150);
        }
        
        // Scroll to a specific level section
        function scrollToLevel(level) {
            const levelSections = document.querySelectorAll('.level-section');
            
            for (const section of levelSections) {
                const levelTitle = section.querySelector('.level-title');
                if (levelTitle) {
                    const levelMatch = levelTitle.textContent.match(/Level (\\d+)/);
                    if (levelMatch && parseInt(levelMatch[1]) === level) {
                        // Apply blur effect before scrolling
                        applyScrollBlur();
                        
                        section.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                        
                        // Add a temporary highlight effect after blur clears
                        setTimeout(() => {
                            const levelHeader = section.querySelector('.level-header');
                            if (levelHeader) {
                                levelHeader.style.transform = 'scale(1.02)';
                                levelHeader.style.boxShadow = '0 0 30px rgba(var(--primary-rgb), 0.6)';
                                setTimeout(() => {
                                    levelHeader.style.transform = '';
                                    levelHeader.style.boxShadow = '';
                                }, 1000);
                            }
                        }, 300);
                        break;
                    }
                }
            }
        }
        
        // Scroll to top of page
        function scrollToTop() {
            // Apply blur effect before scrolling
            applyScrollBlur();
            
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
        
        // Listen for manual scrolling to also apply blur effect
        let scrollTimer;
        window.addEventListener('scroll', () => {
            // Only apply blur if this is manual scrolling (not from our functions)
            if (!isScrolling) {
                applyScrollBlur();
            }
        });
        
        function copySpellId(spellId) {
            // Copy to clipboard
            navigator.clipboard.writeText(spellId).then(function() {
                // Show confirmation popup
                const popup = document.getElementById('copyPopup');
                popup.textContent = `Spell ID ${spellId} copied to clipboard!`;
                popup.classList.add('show');
                
                // Hide popup after 2 seconds
                setTimeout(function() {
                    popup.classList.remove('show');
                }, 2000);
            }).catch(function(err) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = spellId;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                // Show confirmation popup
                const popup = document.getElementById('copyPopup');
                popup.textContent = `Spell ID ${spellId} copied to clipboard!`;
                popup.classList.add('show');
                
                setTimeout(function() {
                    popup.classList.remove('show');
                }, 2000);
            });
        }
        
        // Initialize everything when the page loads
        document.addEventListener('DOMContentLoaded', function() {
            initializeLevelMatrix();
        });
    </script>
</body>
</html>
"""

def fetch_spell_html(class_type: int, base_url: str = BASE_URL) -> str:
    """Fetch HTML for a class's spells from the remote site."""
    
    # Add headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    resp = requests.get(
        base_url,
        params={"a": "spells", "name": "", "type": class_type, "level": 1, "opt": 2},
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.text

def read_local_spell_html(cls: str, local_dir: str) -> Optional[str]:
    """Return HTML from a local file if present."""

    path = os.path.join(local_dir, f"{cls.lower()}.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    # Fallback to a generic sample if available
    sample = os.path.join(local_dir, "sample_table.html")
    if os.path.exists(sample):
        with open(sample, "r", encoding="utf-8") as f:
            return f.read()
    return None

def parse_spell_table(html: str) -> pd.DataFrame:
    """Parse spell table from HTML for alla clone structure."""
    soup = BeautifulSoup(html, 'html.parser')
    spells = []
    
    # Look for level sections in the HTML
    level_headers = soup.find_all(string=lambda text: text and text.strip().startswith('Level:'))
    
    if not level_headers:
        # Fallback: look for "Level X" patterns
        level_headers = soup.find_all(string=lambda text: text and 'Level' in text and any(c.isdigit() for c in text))
    
    for level_text in level_headers:
        try:
            # Extract level number
            level_match = [int(s) for s in level_text.split() if s.isdigit()]
            if not level_match:
                continue
            current_level = level_match[0];
            
            # Find the parent element
            level_element = level_text.parent
            if not level_element:
                continue
            
            # Look for spell data in subsequent elements
            current = level_element
            spell_count = 0
            
            while current and spell_count < 50:  # Safety limit
                current = current.find_next()
                if not current:
                    break
                
                # Stop if we hit the next level
                if current.get_text() and 'Level:' in current.get_text():
                    break
                
                # Look for spell links
                spell_links = current.find_all('a', href=True) if hasattr(current, 'find_all') else []
                
                for link in spell_links:
                    href = link.get('href', '')
                    if not href or 'javascript' in href.lower():
                        continue
                    
                    spell_name = link.get_text().strip()
                    if not spell_name or len(spell_name) < 2:
                        continue
                    
                    # Skip navigation links
                    if spell_name.lower() in ['search', 'reset', 'home', 'main']:
                        continue
                    
                    # Get the table row containing this spell
                    row = link.find_parent('tr')
                    if not row:
                        continue
                    
                    # Extract all cells from the row
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 6:  # Need at least 6 columns for complete data
                        continue
                    
                    # Parse the row data
                    cell_texts = [cell.get_text().strip() for cell in cells]
                    
                    spell_data = {
                        'Level': current_level,
                        'Name': spell_name,
                        'Class': '',
                        'Effect(s)': '',
                        'Mana': '',
                        'Skill': '',
                        'Target Type': '',
                        'Spell ID': '',
                        'Icon': ''
                    }
                    
                    # Look for spell icon in the row
                    for cell in cells:
                        img = cell.find('img')
                        if img and img.get('src'):
                            icon_src = img.get('src')
                            # Convert relative URLs to absolute URLs
                            if icon_src.startswith('/'):
                                spell_data['Icon'] = f"https://alla.clumsysworld.com{icon_src}"
                            elif not icon_src.startswith('http'):
                                spell_data['Icon'] = f"https://alla.clumsysworld.com/{icon_src}"
                            else:
                                spell_data['Icon'] = icon_src
                            break
                    
                    # Map cell data to fields based on position and content
                    # First pass: identify numeric values for mana and spell ID
                    numeric_values = []
                    for cell_text in cell_texts:
                        if cell_text.isdigit():
                            numeric_values.append(int(cell_text))
                    
                    # Sort numeric values to help distinguish mana from spell ID
                    numeric_values.sort()
                    
                    # Process cells in order of priority
                    for i, cell_text in enumerate(cell_texts):
                        if not cell_text or cell_text == '-':
                            continue
                        
                        # Skip the spell name itself
                        if cell_text == spell_name:
                            continue
                        
                        # Class (usually contains class name + level) - strip numbers
                        if any(class_name in cell_text for class_name in ['Magician', 'Wizard', 'Necromancer', 'Enchanter', 'Cleric', 'Druid', 'Shaman', 'Beastlord', 'Ranger', 'Paladin', 'Shadow Knight', 'Warrior', 'Monk', 'Rogue', 'Bard', 'Berserker']):
                            # Strip numbers and extra whitespace from class names
                            import re
                            clean_class = re.sub(r'\d+', '', cell_text).strip()
                            spell_data['Class'] = clean_class
                        
                        # Magic School
                        elif cell_text in ['Divination', 'Abjuration', 'Alteration', 'Evocation', 'Conjuration']:
                            spell_data['Skill'] = cell_text
                    
                    # Second pass: look for target type in remaining unassigned cells
                    for i, cell_text in enumerate(cell_texts):
                        if not cell_text or cell_text == '-' or cell_text.isdigit():
                            continue
                        
                        # Skip already assigned data
                        if (cell_text == spell_name or 
                            cell_text == spell_data['Class'] or 
                            cell_text == spell_data['Skill']):
                            continue
                        
                        # Look for target type - be more permissive but still logical
                        if (not spell_data['Target Type'] and 
                            len(cell_text) >= 3 and 
                            len(cell_text) <= 50):  # Reasonable length range
                            
                            # Check if it looks like a target type
                            lower_text = cell_text.lower();
                            if (any(keyword in lower_text for keyword in [
                                'target', 'self', 'group', 'area', 'caster', 'pet', 'undead', 
                                'ward', 'corpse', 'object', 'teleport', 'summoned', 'beings',
                                'only', 'around', 'effect'
                            ]) or 
                            # Common short target types
                            cell_text in ['Single', 'Group', 'AoE', 'Self']):
                                spell_data['Target Type'] = cell_text;
                                break;
                    
                    # Third pass: assign remaining long text as effects
                    for i, cell_text in enumerate(cell_texts):
                        if (not spell_data['Effect(s)'] and 
                            not cell_text.isdigit() and 
                            len(cell_text) > 10 and
                            cell_text != spell_name and
                            cell_text != spell_data['Class'] and
                            cell_text != spell_data['Skill'] and
                            cell_text != spell_data['Target Type']):
                            spell_data['Effect(s)'] = cell_text
                            break
                    
                    # Handle numeric values (mana and spell ID) with better logic
                    # The rightmost column is typically Spell ID, so work backwards
                    if numeric_values:
                        # Get the last numeric cell (rightmost) as spell ID
                        for j in range(len(cell_texts) - 1, -1, -1):
                            if cell_texts[j].isdigit():
                                if not spell_data['Spell ID']:
                                    spell_data['Spell ID'] = cell_texts[j]
                                    break
                        
                        # Find mana cost (usually smaller number, not the spell ID)
                        for cell_text in cell_texts:
                            if (cell_text.isdigit() and 
                                cell_text != spell_data['Spell ID'] and 
                                1 <= len(cell_text) <= 3 and 
                                int(cell_text) <= 999):
                                if not spell_data['Mana']:
                                    spell_data['Mana'] = cell_text
                                    break

                    spells.append(spell_data)
                    spell_count += 1
                    
        except (ValueError, AttributeError) as e:
            continue
    
    if not spells:
        raise ValueError("No spell data found in HTML")
    
    # Create DataFrame and clean up
    df = pd.DataFrame(spells)
    df = df.drop_duplicates(subset=['Name'], keep='first')
    
    # Sort by level then by name
    df['Level'] = pd.to_numeric(df['Level'], errors='coerce')
    df = df.sort_values(['Level', 'Name'])
    return df;


def _hex_to_rgb(hex_color: str) -> str:
    """Convert #RRGGBB to "R, G, B" string."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
    return "0, 0, 0"


def generate_html(cls: str, df: pd.DataFrame) -> str:
    """Render HTML for a class using the global template."""
    color = CLASS_COLORS.get(cls, '#cccccc')
    color_rgb = _hex_to_rgb(color)

    sections: List[str] = []
    for level, group in df.groupby('Level'):
        cards: List[str] = []
        for _, row in group.iterrows():
            attrs = []
            
            # Add Spell ID as the first attribute with copy button
            if row['Spell ID']:
                attrs.append(f'''
                    <div class="spell-attribute">
                        <span class="attribute-label">Spell ID:</span>
                        <div class="spell-id-container">
                            <span class="attribute-value">{row["Spell ID"]}</span>
                            <button class="copy-btn" onclick="copySpellId('{row['Spell ID']}')" title="Copy Spell ID to clipboard"></button>
                        </div>
                    </div>
                ''')
            
            # Add Mana as an attribute
            if row['Mana']:
                attrs.append(f'''
                    <div class="spell-attribute">
                        <span class="attribute-label">Mana Cost:</span>
                        <span class="attribute-value">{row["Mana"]}</span>
                    </div>
                ''')
            
            # Add School as an attribute
            if row['Skill']:
                attrs.append(f'''
                    <div class="spell-attribute">
                        <span class="attribute-label">Spell School:</span>
                        <span class="attribute-value">{row["Skill"]}</span>
                    </div>
                ''')
            
            # Add Target Type as an attribute with color coding
            if row['Target Type']:
                target_class = ""
                target_type = row['Target Type']
                if target_type in ['Self only', "Caster's pet"]:
                    target_class = " target-self"
                elif target_type in ['Single target', "Target's corpse", 'Summoned beings', 'Undead only']:
                    target_class = " target-single"
                elif target_type in ['Area of effect around the target']:
                    target_class = " target-aoe-target"
                elif target_type in ['Area of effect around the caster']:
                    target_class = " target-aoe-caster"
                elif target_type in ['Group', 'Group target', 'Group teleport']:
                    target_class = " target-group"
                
                attrs.append(f'''
                    <div class="spell-attribute{target_class}">
                        <span class="attribute-label">Target Type:</span>
                        <span class="attribute-value">{row["Target Type"]}</span>
                    </div>
                ''')

            icon_html = (
                f'<img class="spell-icon" src="{row["Icon"]}" alt="icon" />'
                if row['Icon']
                else ''
            )

            card = f"""
            <div class="spell-card">
                <div class="spell-header">
                    <div class="spell-name">{row['Name']}</div>
                    {icon_html}
                </div>
                <div class="spell-body">
                    <div class="spell-attributes">{''.join(attrs)}</div>
                </div>
            </div>
            """
            cards.append(card)

        section = f"""
        <section class="level-section">
            <div class="level-header">
                <h2 class="level-title">Level {int(level)}</h2>
                <div class="level-header-right">
                    <span class="level-count">{len(group)} {'Spell' if len(group) == 1 else 'Spells'}</span>
                    <button class="go-to-top-btn" onclick="scrollToTop()" title="Go to top of page">
                        Top
                    </button>
                </div>
            </div>
            <div class="spells-masonry">
                {''.join(cards)}
            </div>
        </section>
        """
        sections.append(section)

    template = Template(HTML_TEMPLATE)
    html = template.render(
        cls=cls,
        color=color,
        color_rgb=color_rgb,
        content=''.join(sections),
        total_spells=len(df),
        max_level=int(df['Level'].max() if not df.empty else 0),
        schools_count=df['Skill'].nunique(),
    )
    return html


def scrape_class(cls: str, base_url: str, local_dir: Optional[str]) -> pd.DataFrame:
    """Fetch, parse and return spell data for a single class."""
    html = None
    if local_dir:
        html = read_local_spell_html(cls, local_dir)
    if html is None:
        print(f"Fetching {cls} from {base_url}")
        html = fetch_spell_html(CLASSES[cls], base_url=base_url)
        
        # Save raw HTML for debugging
        temp_file = os.path.join(os.path.dirname(__file__), f"temp_{cls.lower()}.html")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved temp HTML to {temp_file}")
    
    return parse_spell_table(html)


def save_html(cls: str, html: str, output_dir: str = '.') -> None:
    """Write HTML to disk."""
    path = os.path.join(output_dir, f"{cls.lower()}_spells.html")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)


def scrape_all(base_url: str, local_dir: Optional[str]) -> None:
    """Scrape spell data for all classes and write HTML files."""
    for cls in CLASSES.keys():
        try:
            df = scrape_class(cls, base_url=base_url, local_dir=local_dir)
            html = generate_html(cls, df)
            save_html(cls, html)
            print(f"Wrote {cls.lower()}_spells.html")
        except Exception as exc:
            print(f"Failed to scrape {cls}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape EverQuest spell data")
    parser.add_argument('--loop', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=3600, help='Seconds between runs when using --loop')
    parser.add_argument('--base-url', default=BASE_URL, help='Base URL of the spell site')
    parser.add_argument('--local-dir', default=None, help='Directory of local HTML files')
    args = parser.parse_args()

    def run_once():
        scrape_all(base_url=args.base_url, local_dir=args.local_dir)

    if args.loop:
        try:
            while True:
                run_once()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
    else:
        run_once()


if __name__ == '__main__':
    main()
