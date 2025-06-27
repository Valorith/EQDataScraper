#!/usr/bin/env python3
import os
import time
import argparse
import logging
import tempfile
from typing import Dict, Optional, List

import requests
import pandas as pd
from bs4 import BeautifulSoup
from jinja2 import Template

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ cls }} Spells - Norrath Compendium</title>
    <meta name="description" content="Complete {{ cls }} spell compendium for EverQuest - Browse all {{ total_spells }} spells with detailed information">
    
    <!-- Preconnect to external domains for performance -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    
    <!-- Import fonts with display swap for better performance -->
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500;600;700&family=Crimson+Text:wght@400;600&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: {{ color }};
            --primary-rgb: {{ color_rgb }};
            --bg-dark: #0a0e1a;
            --bg-darker: #050810;
            --bg-glass: rgba(16, 20, 32, 0.85);
            --card-bg: rgba(42, 46, 54, 0.95);
            --text-light: #e2e8f0;
            --text-dark: #f8fafc;
            --text-muted: #94a3b8;
            --shadow-color: rgba(0, 0, 0, 0.4);
            --shadow-heavy: rgba(0, 0, 0, 0.6);
            --border-glass: rgba(255, 255, 255, 0.1);
            --accent-glow: rgba(var(--primary-rgb), 0.3);
        }
        
        /* Reset and base styles */
        *, *::before, *::after { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        html {
            scroll-behavior: smooth;
            font-size: 16px;
        }
        
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: 
                var(--bg-darker),
                radial-gradient(ellipse at 25% 25%, rgba(var(--primary-rgb), 0.15) 0%, transparent 60%),
                radial-gradient(ellipse at 75% 25%, rgba(var(--primary-rgb), 0.12) 0%, transparent 60%),
                radial-gradient(ellipse at 25% 75%, rgba(var(--primary-rgb), 0.08) 0%, transparent 60%),
                radial-gradient(ellipse at 75% 75%, rgba(var(--primary-rgb), 0.10) 0%, transparent 60%),
                linear-gradient(135deg, var(--bg-darker) 0%, var(--bg-dark) 100%);
            background-attachment: fixed;
            min-height: 100vh;
            color: var(--text-light);
            line-height: 1.6;
            overflow-x: hidden;
            position: relative;
        }
        
        /* Animated background grain effect */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><defs><pattern id="grain" width="200" height="200" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="0.5" fill="rgba(255,255,255,0.02)"/><circle cx="150" cy="150" r="0.3" fill="rgba(147,112,219,0.03)"/><circle cx="150" cy="50" r="0.4" fill="rgba(255,255,255,0.015)"/><circle cx="50" cy="150" r="0.3" fill="rgba(147,112,219,0.025)"/></pattern></defs><rect width="200" height="200" fill="url(%23grain)"/></svg>');
            pointer-events: none;
            z-index: 1;
            animation: grainMove 20s linear infinite;
        }
        
        @keyframes grainMove {
            0% { transform: translate(0, 0); }
            25% { transform: translate(-2px, 2px); }
            50% { transform: translate(2px, -2px); }
            75% { transform: translate(-1px, -1px); }
            100% { transform: translate(0, 0); }
        }
        
        .main-container {
            position: relative;
            z-index: 2;
            padding: 2rem 1rem;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        /* Hero Section */
        .hero-section {
            text-align: center;
            margin-bottom: 4rem;
            position: relative;
            padding: 2rem 0;
        }
        
        .hero-section::before {
            content: '';
            position: absolute;
            top: -50%;
            left: 50%;
            transform: translateX(-50%);
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(var(--primary-rgb), 0.4) 0%, transparent 70%);
            border-radius: 50%;
            filter: blur(80px);
            z-index: -1;
            animation: heroGlow 4s ease-in-out infinite alternate;
        }
        
        @keyframes heroGlow {
            0% { opacity: 0.7; transform: translateX(-50%) scale(1); }
            100% { opacity: 1; transform: translateX(-50%) scale(1.1); }
        }
        
        .home-button {
            position: absolute;
            top: 0;
            left: 0;
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.8));
            color: white;
            border: none;
            border-radius: 16px;
            padding: 0.75rem 1.25rem;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 4px 20px rgba(var(--primary-rgb), 0.3);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .home-button::before {
            content: '←';
            font-size: 1.2em;
            transition: transform 0.3s ease;
        }
        
        .home-button:hover {
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.95), var(--primary-color));
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 8px 30px rgba(var(--primary-rgb), 0.5);
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
        }
        
        .home-button:hover::before {
            transform: translateX(-3px);
        }
        
        .class-title {
            font-family: 'Cinzel', serif;
            font-size: clamp(3rem, 8vw, 5.5rem);
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-color) 0%, rgba(255,255,255,0.9) 50%, var(--primary-color) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 1rem 0;
            text-shadow: 0 0 40px rgba(var(--primary-rgb), 0.6);
            animation: titleGlow 3s ease-in-out infinite alternate;
            letter-spacing: 2px;
        }
        
        @keyframes titleGlow {
            0% { filter: drop-shadow(0 0 20px rgba(var(--primary-rgb), 0.5)); }
            100% { filter: drop-shadow(0 0 40px rgba(var(--primary-rgb), 0.8)) drop-shadow(0 0 60px rgba(var(--primary-rgb), 0.4)); }
        }
        
        .class-subtitle {
            font-size: 1.5rem;
            color: var(--text-muted);
            font-weight: 300;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-top: 0.5rem;
        }
        
        /* Statistics Dashboard */
        .stats-dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
            margin-bottom: 4rem;
        }
        
        .stat-card {
            background: linear-gradient(145deg, var(--bg-glass), rgba(255,255,255,0.03));
            backdrop-filter: blur(25px);
            border: 1px solid var(--border-glass);
            border-radius: 24px;
            padding: 2.5rem;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-rgb), 0.15), transparent);
            transition: left 0.6s ease;
        }
        
        .stat-card:hover::before {
            left: 100%;
        }
        
        .stat-card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 25px 50px rgba(var(--primary-rgb), 0.3);
            border-color: rgba(var(--primary-rgb), 0.4);
        }
        
        .stat-number {
            font-size: 4rem;
            font-weight: 700;
            color: var(--primary-color);
            display: block;
            margin-bottom: 0.5rem;
            font-family: 'Cinzel', serif;
            text-shadow: 0 0 20px rgba(var(--primary-rgb), 0.5);
        }
        
        .stat-label {
            font-size: 1.1rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
            font-weight: 500;
        }
        
        /* Enhanced Level Navigator */
        .level-navigator {
            background: linear-gradient(145deg, var(--bg-glass), rgba(255,255,255,0.03));
            backdrop-filter: blur(25px);
            border: 1px solid var(--border-glass);
            border-radius: 24px;
            padding: 2.5rem;
            margin-bottom: 4rem;
            position: relative;
            overflow: hidden;
        }
        
        .level-nav-title {
            font-family: 'Cinzel', serif;
            font-size: 2rem;
            font-weight: 600;
            color: var(--primary-color);
            text-align: center;
            margin-bottom: 2rem;
            text-shadow: 0 0 20px rgba(var(--primary-rgb), 0.4);
        }
        
        .level-matrix {
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            grid-template-rows: repeat(6, 1fr);
            gap: 0.5rem;
            max-width: 600px;
            margin: 0 auto;
            padding: 1rem;
        }
        
        .level-cell {
            aspect-ratio: 1;
            background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
            color: var(--text-muted);
            min-height: 45px;
            font-family: 'Inter', sans-serif;
            text-align: center;
            user-select: none;
        }
        
        .level-cell.available {
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.25), rgba(var(--primary-rgb), 0.15));
            border-color: rgba(var(--primary-rgb), 0.5);
            color: var(--text-light);
            font-weight: 700;
            box-shadow: 0 0 15px rgba(var(--primary-rgb), 0.2);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        }
        
        .level-cell.available:hover {
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.8));
            color: white;
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 8px 25px rgba(var(--primary-rgb), 0.6);
            text-shadow: 0 0 8px rgba(255, 255, 255, 0.9);
            border-color: var(--primary-color);
        }
        
        .level-cell.available:active {
            transform: translateY(-1px) scale(1.02);
            box-shadow: 0 4px 15px rgba(var(--primary-rgb), 0.8);
        }
        
        .level-cell.disabled {
            background: linear-gradient(135deg, rgba(100, 100, 100, 0.1), rgba(80, 80, 80, 0.05));
            border-color: rgba(100, 100, 100, 0.15);
            color: rgba(180, 180, 180, 0.4);
            cursor: not-allowed;
            opacity: 0.5;
        }
        
        .level-cell.disabled:hover {
            transform: none;
            box-shadow: none;
            background: linear-gradient(135deg, rgba(100, 100, 100, 0.1), rgba(80, 80, 80, 0.05));
            border-color: rgba(100, 100, 100, 0.15);
        }
        
        .level-cell.current {
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.9)) !important;
            color: white !important;
            border-color: rgba(255, 255, 255, 0.8) !important;
            box-shadow: 0 0 20px rgba(var(--primary-rgb), 0.8) !important;
            text-shadow: 0 0 10px rgba(255, 255, 255, 1) !important;
            animation: currentLevel 2s ease-in-out infinite alternate;
        }
        
        @keyframes currentLevel {
            0% { box-shadow: 0 0 20px rgba(var(--primary-rgb), 0.8); }
            100% { box-shadow: 0 0 30px rgba(var(--primary-rgb), 1), 0 0 40px rgba(var(--primary-rgb), 0.6); }
        }
        
        /* Enhanced Spell Cards */
        .level-section {
            margin-bottom: 5rem;
            opacity: 0;
            animation: fadeInUp 0.8s ease-out forwards;
            scroll-margin-top: 120px;
        }
        
        .level-section:nth-child(even) { animation-delay: 0.1s; }
        .level-section:nth-child(odd) { animation-delay: 0.2s; }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(40px);
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
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.15), rgba(var(--primary-rgb), 0.05));
            backdrop-filter: blur(20px);
            border: 1px solid rgba(var(--primary-rgb), 0.3);
            border-radius: 20px;
            padding: 2rem 2.5rem;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }
        
        .level-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary-color), rgba(var(--primary-rgb), 0.6), var(--primary-color));
        }
        
        .level-title {
            font-family: 'Cinzel', serif;
            font-size: 2.5rem;
            font-weight: 600;
            color: var(--primary-color);
            text-shadow: 0 0 20px rgba(var(--primary-rgb), 0.4);
        }
        
        .level-header-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .level-count {
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.9rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
        }
        
        .go-to-top-btn {
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.8));
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .go-to-top-btn:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 8px 20px rgba(var(--primary-rgb), 0.4);
        }
        
        .go-to-top-btn::after {
            content: '↑';
            font-size: 1.2em;
        }
        
        /* Modern Spell Cards Grid */
        .spells-masonry {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 1.5rem;
            align-items: start;
        }
        
        .spell-card {
            background: linear-gradient(145deg, var(--card-bg), rgba(255,255,255,0.05));
            backdrop-filter: blur(25px);
            border-radius: 24px;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            border: 2px solid rgba(var(--primary-rgb), 0.2);
            box-shadow: 0 10px 40px var(--shadow-color);
        }
        
        .spell-card:hover {
            transform: translateY(-8px) rotate(0.5deg);
            box-shadow: 0 30px 60px rgba(var(--primary-rgb), 0.3);
            border-color: rgba(var(--primary-rgb), 0.6);
        }
        
        .spell-header {
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.8));
            color: white;
            padding: 1.5rem 2rem;
            position: relative;
            overflow: hidden;
        }
        
        .spell-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transition: left 0.6s ease;
        }
        
        .spell-card:hover .spell-header::before {
            left: 100%;
        }
        
        .spell-icon {
            position: absolute;
            top: 15px;
            right: 20px;
            width: 56px;
            height: 56px;
            border-radius: 16px;
            border: 3px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.1);
            padding: 4px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .spell-icon:hover {
            transform: scale(1.15);
            border-color: rgba(255,255,255,0.8);
            box-shadow: 0 0 25px rgba(255,255,255,0.5);
        }
        
        .spell-name {
            font-family: 'Cinzel', serif;
            font-size: 1.75rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            padding-right: 80px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            line-height: 1.2;
        }
        
        .spell-level {
            font-size: 1rem;
            opacity: 0.9;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .spell-body {
            padding: 2rem;
            color: var(--text-dark);
        }
        
        .spell-attributes {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .spell-attribute {
            display: flex;
            flex-direction: column;
            background: rgba(var(--primary-rgb), 0.05);
            padding: 1rem;
            border-radius: 12px;
            border-left: 4px solid var(--primary-color);
            position: relative;
            transition: all 0.3s ease;
        }
        
        .spell-attribute:hover {
            background: rgba(var(--primary-rgb), 0.1);
            transform: translateX(3px);
        }
        
        .attribute-label {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: 'Inter', sans-serif;
        }
        
        .attribute-value {
            font-size: 1rem;
            font-weight: 500;
            color: var(--text-dark);
            font-family: 'Crimson Text', serif;
        }
        
        /* Enhanced Target Type Color Coding */
        .target-self { 
            background: rgba(255, 215, 0, 0.1) !important; 
            border-left-color: #ffd700 !important; 
        }
        .target-single { 
            background: rgba(255, 68, 68, 0.1) !important; 
            border-left-color: #ff4444 !important; 
        }
        .target-aoe-target { 
            background: rgba(34, 197, 94, 0.1) !important; 
            border-left-color: #22c55e !important; 
        }
        .target-aoe-caster { 
            background: rgba(59, 130, 246, 0.1) !important; 
            border-left-color: #3b82f6 !important; 
        }
        .target-group { 
            background: rgba(168, 85, 247, 0.1) !important; 
            border-left-color: #a855f7 !important; 
        }
        
        /* Enhanced Copy Button */
        .spell-id-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .copy-btn {
            background: linear-gradient(135deg, var(--primary-color), rgba(var(--primary-rgb), 0.8));
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.5rem;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-left: 0.75rem;
            width: 36px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            backdrop-filter: blur(10px);
        }
        
        .copy-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(var(--primary-rgb), 0.5);
        }
        
        .copy-btn::before {
            content: '📋';
            font-size: 1rem;
        }
        
        /* Copy Popup */
        .copy-popup {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--primary-color);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            font-weight: 600;
            z-index: 1000;
            opacity: 0;
            transition: all 0.3s ease;
            pointer-events: none;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(20px);
        }
        
        .copy-popup.show {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1.05);
        }
        
        /* Scroll Effects */
        .scroll-blur .spell-card {
            filter: blur(2px);
            opacity: 0.8;
            transform: scale(0.99);
        }
        
        .scroll-blur .level-section {
            filter: blur(2px);
            opacity: 0.8;
        }
        
        /* Responsive Design */
        @media (max-width: 1200px) {
            .spells-masonry {
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            }
        }
        
        @media (max-width: 768px) {
            .main-container {
                padding: 1rem;
            }
            
            .class-title { 
                font-size: 3rem; 
            }
            
            .stats-dashboard { 
                grid-template-columns: 1fr; 
                gap: 1rem;
            }
            
            .spells-masonry { 
                grid-template-columns: 1fr; 
            }
            
            .spell-attributes { 
                grid-template-columns: 1fr; 
            }
            
            .level-matrix { 
                grid-template-columns: repeat(8, 1fr);
                grid-template-rows: repeat(8, 1fr);
                max-width: 500px;
            }
            
            .level-navigator { 
                padding: 1.5rem; 
            }
            
            .level-header { 
                flex-direction: column; 
                gap: 1rem; 
                text-align: center; 
                padding: 1.5rem;
            }
            
            .home-button { 
                position: static; 
                margin: 0 auto 1.5rem auto; 
            }
        }
        
        @media (max-width: 480px) {
            .level-matrix { 
                grid-template-columns: repeat(6, 1fr);
                grid-template-rows: repeat(10, 1fr);
                gap: 0.25rem;
                max-width: 400px;
            }
            
            .level-cell { 
                font-size: 0.8rem; 
                min-height: 40px; 
            }
            
            .spell-card {
                border-radius: 16px;
            }
            
            .spell-body {
                padding: 1.5rem;
            }
        }
        
        /* Performance optimizations */
        .spell-card {
            will-change: transform;
        }
        
        .level-cell {
            will-change: transform;
        }
        
        /* Accessibility improvements */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            :root {
                --text-light: #ffffff;
                --text-dark: #ffffff;
                --border-glass: rgba(255, 255, 255, 0.3);
            }
        }
    </style>
</head>
<body>
    <div class="main-container">
        <header class="hero-section">
            <a href="index.html" class="home-button" aria-label="Return to home page">
                <span>Home</span>
            </a>
            <h1 class="class-title">{{ cls }}</h1>
            <p class="class-subtitle">Spell Compendium</p>
        </header>
        
        <section class="stats-dashboard" aria-label="Spell statistics">
            <div class="stat-card" tabindex="0">
                <span class="stat-number" aria-label="{{ total_spells }} total spells">{{ total_spells }}</span>
                <span class="stat-label">Total Spells</span>
            </div>
            <div class="stat-card" tabindex="0">
                <span class="stat-number" aria-label="Maximum level {{ max_level }}">{{ max_level }}</span>
                <span class="stat-label">Max Level</span>
            </div>
            <div class="stat-card" tabindex="0">
                <span class="stat-number" aria-label="{{ schools_count }} magic schools">{{ schools_count }}</span>
                <span class="stat-label">Magic Schools</span>
            </div>
        </section>
        
        <nav class="level-navigator" aria-label="Level navigation">
            <h2 class="level-nav-title">Quick Level Navigation</h2>
            <div class="level-matrix" id="levelMatrix" role="grid" aria-label="Level selection grid">
                <!-- Level cells will be populated by JavaScript -->
            </div>
        </nav>
        
        <main>
            {{ content|safe }}
        </main>
    </div>
    
    <!-- Copy confirmation popup -->
    <div id="copyPopup" class="copy-popup" role="alert" aria-live="polite">
        Spell ID copied to clipboard!
    </div>
    
    <script>
        (() => {
            'use strict';
            
            let isScrolling = false;
            let scrollTimeout;
            
            // Initialize level navigation matrix
            function initializeLevelMatrix() {
                const matrix = document.getElementById('levelMatrix');
                if (!matrix) return;
                
                const availableLevels = new Set();
                
                // Find all level sections on the page
                document.querySelectorAll('.level-section').forEach(section => {
                    const levelTitle = section.querySelector('.level-title');
                    if (levelTitle) {
                        const levelMatch = levelTitle.textContent.match(/Level (\\d+)/);
                        if (levelMatch) {
                            availableLevels.add(parseInt(levelMatch[1], 10));
                        }
                    }
                });
                
                // Create level cells (6 rows x 10 columns = 60 levels)
                const fragment = document.createDocumentFragment();
                for (let i = 1; i <= 60; i++) {
                    const cell = document.createElement('button');
                    cell.className = 'level-cell';
                    cell.textContent = String(i);
                    cell.setAttribute('data-level', String(i));
                    cell.type = 'button';
                    
                    if (availableLevels.has(i)) {
                        cell.classList.add('available');
                        cell.setAttribute('aria-label', `Jump to level ${i} spells`);
                        cell.setAttribute('title', `Click to view level ${i} spells`);
                        cell.addEventListener('click', () => {
                            // Add visual feedback
                            cell.style.transform = 'scale(0.95)';
                            setTimeout(() => {
                                cell.style.transform = '';
                            }, 150);
                            scrollToLevel(i);
                        });
                    } else {
                        cell.classList.add('disabled');
                        cell.setAttribute('aria-label', `No spells available at level ${i}`);
                        cell.setAttribute('title', `No spells at level ${i}`);
                        cell.disabled = true;
                    }
                    
                    fragment.appendChild(cell);
                }
                
                matrix.appendChild(fragment);
            }
            
            // Apply blur effect during scrolling
            function applyScrollBlur() {
                if (!isScrolling) {
                    isScrolling = true;
                    document.body.classList.add('scroll-blur');
                }
                
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    isScrolling = false;
                    document.body.classList.remove('scroll-blur');
                }, 150);
            }
            
            // Scroll to a specific level section
            function scrollToLevel(level) {
                const sections = document.querySelectorAll('.level-section');
                
                for (const section of sections) {
                    const levelTitle = section.querySelector('.level-title');
                    if (levelTitle) {
                        const levelMatch = levelTitle.textContent.match(/Level (\\d+)/);
                        if (levelMatch && parseInt(levelMatch[1], 10) === level) {
                            applyScrollBlur();
                            
                            section.scrollIntoView({
                                behavior: 'smooth',
                                block: 'start'
                            });
                            
                            // Highlight effect
                            setTimeout(() => {
                                const levelHeader = section.querySelector('.level-header');
                                if (levelHeader) {
                                    levelHeader.style.transform = 'scale(1.02)';
                                    levelHeader.style.boxShadow = '0 0 40px rgba(var(--primary-rgb), 0.6)';
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
                applyScrollBlur();
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }
            
            // Copy spell ID to clipboard
            function copySpellId(spellId) {
                const popup = document.getElementById('copyPopup');
                
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(spellId)
                        .then(() => showCopyPopup(popup, spellId))
                        .catch(() => fallbackCopy(spellId, popup));
                } else {
                    fallbackCopy(spellId, popup);
                }
            }
            
            function fallbackCopy(spellId, popup) {
                const textArea = document.createElement('textarea');
                textArea.value = spellId;
                textArea.style.position = 'absolute';
                textArea.style.left = '-9999px';
                document.body.appendChild(textArea);
                textArea.select();
                
                try {
                    document.execCommand('copy');
                    showCopyPopup(popup, spellId);
                } catch (err) {
                    console.error('Failed to copy text: ', err);
                } finally {
                    document.body.removeChild(textArea);
                }
            }
            
            function showCopyPopup(popup, spellId) {
                if (!popup) return;
                
                popup.textContent = `Spell ID ${spellId} copied to clipboard!`;
                popup.classList.add('show');
                
                setTimeout(() => {
                    popup.classList.remove('show');
                }, 2500);
            }
            
            // Function to update current level indicator
            function updateCurrentLevel() {
                const sections = document.querySelectorAll('.level-section');
                const levelCells = document.querySelectorAll('.level-cell.available');
                const scrollPosition = window.scrollY + window.innerHeight / 3;
                
                let currentLevel = null;
                
                // Find which section is currently in view
                sections.forEach(section => {
                    const rect = section.getBoundingClientRect();
                    const top = rect.top + window.scrollY;
                    
                    if (scrollPosition >= top) {
                        const levelTitle = section.querySelector('.level-title');
                        if (levelTitle) {
                            const levelMatch = levelTitle.textContent.match(/Level (\\d+)/);
                            if (levelMatch) {
                                currentLevel = parseInt(levelMatch[1], 10);
                            }
                        }
                    }
                });
                
                // Update level cell highlighting
                levelCells.forEach(cell => {
                    const cellLevel = parseInt(cell.getAttribute('data-level'), 10);
                    if (cellLevel === currentLevel) {
                        cell.classList.add('current');
                    } else {
                        cell.classList.remove('current');
                    }
                });
            }
            
            // Listen for scroll events
            let scrollTimer;
            window.addEventListener('scroll', () => {
                if (!isScrolling) {
                    applyScrollBlur();
                }
                
                // Update current level indicator
                clearTimeout(scrollTimer);
                scrollTimer = setTimeout(updateCurrentLevel, 100);
            }, { passive: true });
            
            // Make functions available globally
            window.scrollToLevel = scrollToLevel;
            window.scrollToTop = scrollToTop;
            window.copySpellId = copySpellId;
            
            // Initialize when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    initializeLevelMatrix();
                    // Initialize current level after a short delay
                    setTimeout(updateCurrentLevel, 500);
                });
            } else {
                initializeLevelMatrix();
                // Initialize current level after a short delay
                setTimeout(updateCurrentLevel, 500);
            }
            
            // Performance optimization: preload critical resources
            const preloadCritical = () => {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.as = 'style';
                link.href = 'https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&display=swap';
                document.head.appendChild(link);
            };
            
            // Run preload after initial render
            requestAnimationFrame(preloadCritical);
        })();
    </script>
</body>
</html>
"""

def fetch_spell_html(class_type: int, base_url: str = BASE_URL) -> str:
    """Fetch HTML for a class's spells from the remote site."""
    
    # Add headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        logger.info(f"Fetching spell data for class type {class_type} from {base_url}")
        resp = session.get(
            base_url,
            params={"a": "spells", "name": "", "type": class_type, "level": 1, "opt": 2},
            timeout=30,
        )
        resp.raise_for_status()
        
        if len(resp.text) < 1000:
            raise ValueError(f"Received suspiciously short response ({len(resp.text)} chars)")
            
        logger.info(f"Successfully fetched {len(resp.text)} characters of HTML")
        return resp.text
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching data for class type {class_type}")
        raise ConnectionError("Request timed out after 30 seconds")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error for class type {class_type}: {e}")
        raise ConnectionError(f"Unable to connect to {base_url}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code} for class type {class_type}")
        raise ConnectionError(f"Server returned error {e.response.status_code}")
    except Exception as e:
        logger.error(f"Unexpected error fetching data for class type {class_type}: {e}")
        raise
    finally:
        session.close()

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
    if not html or len(html) < 100:
        raise ValueError("HTML content is too short or empty")
        
    try:
        soup = BeautifulSoup(html, 'html.parser')
    except Exception as e:
        logger.error(f"Failed to parse HTML with BeautifulSoup: {e}")
        raise ValueError(f"Invalid HTML content: {e}")
        
    spells = []
    logger.info("Starting spell table parsing")
    
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
            logger.debug(f"Skipping level section due to parsing error: {e}")
            continue
        except Exception as e:
            logger.warning(f"Unexpected error parsing level section: {e}")
            continue
    
    if not spells:
        logger.error("No spell data found in HTML")
        # Save problematic HTML for debugging
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html[:5000])  # First 5000 chars
            logger.error(f"Saved problematic HTML snippet to {f.name}")
        raise ValueError("No spell data found in HTML - possible structure change")
    
    # Create DataFrame and clean up
    try:
        df = pd.DataFrame(spells)
        
        if df.empty:
            raise ValueError("Created empty DataFrame from spell data")
            
        logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        
        # Remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates(subset=['Name'], keep='first')
        final_count = len(df)
        
        if initial_count != final_count:
            logger.info(f"Removed {initial_count - final_count} duplicate spells")
        
        # Sort by level then by name
        df['Level'] = pd.to_numeric(df['Level'], errors='coerce')
        df = df.sort_values(['Level', 'Name'])
        
        # Validate data quality
        null_names = df['Name'].isnull().sum()
        if null_names > 0:
            logger.warning(f"Found {null_names} spells with null names")
            
        logger.info(f"Final dataset: {len(df)} spells, levels {df['Level'].min()}-{df['Level'].max()}")
        return df
        
    except Exception as e:
        logger.error(f"Failed to create or process DataFrame: {e}")
        raise ValueError(f"Data processing failed: {e}")


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
        
        # Save raw HTML for debugging in system temp directory
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=f"_{cls.lower()}.html", delete=False, encoding="utf-8") as f:
                f.write(html)
                temp_file = f.name
            logger.info(f"Saved temp HTML to {temp_file}")
        except Exception as e:
            logger.warning(f"Failed to save temp HTML: {e}")
            temp_file = "<temp file creation failed>"
    
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
