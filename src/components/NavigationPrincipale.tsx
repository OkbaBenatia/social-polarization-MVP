"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { BasculeTheme } from "./BasculeTheme";

const PAGES = [
  { href: "/", libelle: "Vue d'ensemble" },
  { href: "/sources", libelle: "Sources étudiées" },
  { href: "/reseau", libelle: "Réseau" },
  { href: "/communautes", libelle: "Communautés" },
  { href: "/contenu", libelle: "Analyse du contenu" },
  { href: "/sentiments", libelle: "Sentiments et émotions" },
  { href: "/discours-haineux", libelle: "Discours haineux" },
  { href: "/propagation", libelle: "Propagation" },
  { href: "/methodologie", libelle: "Méthodologie" },
];

export function NavigationPrincipale() {
  const chemin = usePathname();
  const [ouvert, setOuvert] = useState(false);

  const estActif = (href: string) =>
    href === "/" ? chemin === "/" : chemin.startsWith(href);

  return (
    <header className="sticky top-0 z-40 border-b border-ardoise-200 bg-white/90 backdrop-blur dark:border-ardoise-800 dark:bg-ardoise-950/90">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="flex h-16 items-center justify-between gap-4">
          <Link href="/" className="flex min-w-0 items-center gap-3">
            <Image
              src="/app-icon.png"
              alt=""
              aria-hidden="true"
              width={36}
              height={36}
              priority
              className="h-9 w-9 shrink-0 rounded-md object-cover"
            />
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-ardoise-900 dark:text-white">
                Polarisation et discours de haine
              </span>
              <span className="block truncate text-xs text-ardoise-500 dark:text-ardoise-400">
                MVP académique — analyse de réseaux sociaux
              </span>
            </span>
          </Link>

          <div className="flex items-center gap-2">
            <BasculeTheme />
            <button
              type="button"
              onClick={() => setOuvert((valeur) => !valeur)}
              aria-expanded={ouvert}
              aria-controls="menu-principal"
              className="rounded-md border border-ardoise-200 px-3 py-2 text-sm font-medium text-ardoise-700 lg:hidden dark:border-ardoise-700 dark:text-ardoise-200"
            >
              {ouvert ? "Fermer" : "Menu"}
            </button>
          </div>
        </div>

        <nav
          id="menu-principal"
          aria-label="Navigation principale"
          className={`${ouvert ? "block" : "hidden"} pb-3 lg:block`}
        >
          <ul className="flex flex-col gap-1 lg:-mb-px lg:flex-row lg:gap-1 lg:overflow-x-auto">
            {PAGES.map((page) => (
              <li key={page.href}>
                <Link
                  href={page.href}
                  onClick={() => setOuvert(false)}
                  aria-current={estActif(page.href) ? "page" : undefined}
                  className={`block whitespace-nowrap rounded-md px-3 py-2 text-sm transition-colors lg:rounded-none lg:border-b-2 ${
                    estActif(page.href)
                      ? "bg-ardoise-100 font-medium text-ardoise-900 lg:bg-transparent lg:border-teal-600 dark:bg-ardoise-800 dark:text-white lg:dark:bg-transparent"
                      : "text-ardoise-600 hover:bg-ardoise-100 lg:border-transparent lg:hover:bg-transparent lg:hover:border-ardoise-300 dark:text-ardoise-400 dark:hover:bg-ardoise-900 lg:dark:hover:bg-transparent"
                  }`}
                >
                  {page.libelle}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}
