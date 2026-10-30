# Markdown VS Other Note Formats

A tiny sample note. It exercises every marker the tool understands: both
emphasis markers, gloss tokens, a table that must stay English, and fold
blocks. `before.md` is what an AI writes; `after.md` is what the tool makes
of it.

## TOC (فهرست)

- [1. Intro (مقدمه)](#1-intro-مقدمه)
- [2. Markdown VS Word](#2-markdown-vs-word)
- [3. Pitfalls (تله ها)](#3-pitfalls-تله-ها)
- [4. Exercises (تمرین ها)](#4-exercises-تمرین-ها)

## 1. Intro (مقدمه)

Markdown = plain text plus a few markers. !!The file IS the note!! - no
database, no app owns it.

- One file, one format → `git diff` shows every changed line ¹ , no extra tool
- Any editor opens it ² , even Notepad on a borrowed PC

¹ گیت تغییرات را خط به خط نشان میدهد - git shows each changed line, because the file is only text

² هر ویرایشگری بازش میکند - any editor opens it, so there is nothing to install or sign in to

## 2. Markdown VS Word

| Format | Diff | Lock-in | Persian RTL |
|---|---|---|---|
| Markdown | ✅ line by line | none ¹ | needs this tool |
| Word (.docx) | ❌ binary | MS Word only | built in |
| Notion | ❌ server side | Notion account | built in |
| Raw HTML | ⚠️ tags = noise | none | `dir="rtl"` by hand |

¹ در ورد فقط خود ورد فایل را درست میخواند - in Word only Word reads the file correctly, while every reader agrees on plain text

- Word, Notion = content lives !!inside a program!!
- Markdown = content lives in a text file that the program only reads
- ^^You cannot diff a .docx^^ → two editors on one binary file ² overwrite each other

² دو ویرایشگر روی یک فایل باینری کار هم را پاک میکنند - two editors on one binary file silently overwrite each other

## 3. Pitfalls (تله ها)

> [!NOTE]
> Every line below is a trap found while writing real notes.

- ^^GitHub ignores your CSS^^ → view the styled note in VS Code or a browser ¹ , not on GitHub
- A gloss token needs a space on BOTH sides ² , or it is not a token
- One Persian digit inside English text flips the whole paragraph RTL ³ , so always ASCII 0-9

¹ گیت هاب استایل لینک شده را حذف میکند - GitHub strips the linked stylesheet, so the colors only exist locally

² بدون فاصله توکن شناخته نمیشود - `copy¹` reads as an exponent, `copy ¹ ` is a gloss

³ رقم فارسی داخل بلوک عربی است - U+06F0 to U+06F9 belong to the Arabic block, one stray digit turns a whole English paragraph RTL

^! Why is fold content forced LTR?

A fold usually holds code or an answer, so the color stage wraps its body in a
`dir="ltr"` div. Persian prose inside a fold therefore stays left aligned.
Delete that one wrapper if you write prose folds.

!^

## 4. Exercises (تمرین ها)

**Ex 1** - یک پاراگراف انگلیسی با یک واژه سخت بنویس و با پاورقی توضیح بده.

^!

A view materializes one saved query ¹ , so it costs storage but no recompute.

¹ the stored result trades disk for speed

!^

**Ex 2** - همان پاراگراف را با ترجمه کامل فارسی بنویس و تعداد کاراکتر ها را مقایسه کن.

^!

An inline translation costs 5 to 10 times the tokens of a gloss and breaks the
Latin run inside an RTL line. The gloss keeps both languages readable.

!^
