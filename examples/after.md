<link rel="stylesheet" href="../md.css">

<div dir="rtl">

# Markdown VS Other Note Formats

</div>

A tiny sample note. It exercises every marker the tool understands: both
emphasis markers, gloss tokens, a table that must stay English, and fold
blocks. `before.md` is what an AI writes; `after.md` is what the tool makes
of it.

<div dir="rtl">

## TOC (فهرست)

</div>

<div dir="rtl">

- [1. Intro (مقدمه)](#1-intro-مقدمه)
- [2. Markdown VS Word](#2-markdown-vs-word)
- [3. Pitfalls (تله ها)](#3-pitfalls-تله-ها)
- [4. Exercises (تمرین ها)](#4-exercises-تمرین-ها)

</div>

<div dir="rtl">

## 1. Intro (مقدمه)

</div>

Markdown = plain text plus a few markers. <span class="hy">The file IS the note</span> - no
database, no app owns it.

- One file, one format → `git diff` shows every changed line <span class="p s22">¹</span> , no extra tool
- Any editor opens it <span class="p s22">²</span> , even Notepad on a borrowed PC

<div dir="rtl">

<span class="g s22">¹</span> گیت تغییرات را خط به خط نشان میدهد - git shows each changed line, because the file is only text

</div>

<div dir="rtl">

<span class="g s22">²</span> هر ویرایشگری بازش میکند - any editor opens it, so there is nothing to install or sign in to

</div>

<div dir="rtl">

## 2. Markdown VS Word

</div>

| Format | Diff | Lock-in | Persian RTL |
|---|---|---|---|
| Markdown | ✅ line by line | none <span class="p s22">¹</span> | needs this tool |
| Word (.docx) | ❌ binary | MS Word only | built in |
| Notion | ❌ server side | Notion account | built in |
| Raw HTML | ⚠️ tags = noise | none | `dir="rtl"` by hand |

<div dir="rtl">

<span class="g s22">¹</span> در ورد فقط خود ورد فایل را درست میخواند - in Word only Word reads the file correctly, while every reader agrees on plain text

</div>

- Word, Notion = content lives <span class="hy">inside a program</span>
- Markdown = content lives in a text file that the program only reads
- <span class="r">You cannot diff a .docx</span> → two editors on one binary file <span class="p s22">²</span> overwrite each other

<div dir="rtl">

<span class="g s22">²</span> دو ویرایشگر روی یک فایل باینری کار هم را پاک میکنند - two editors on one binary file silently overwrite each other

</div>

<div dir="rtl">

## 3. Pitfalls (تله ها)

</div>

> [!NOTE]
> Every line below is a trap found while writing real notes.

- <span class="r">GitHub ignores your CSS</span> → view the styled note in VS Code or a browser <span class="p s22">¹</span> , not on GitHub
- A gloss token needs a space on BOTH sides <span class="p s22">²</span> , or it is not a token
- One Persian digit inside English text flips the whole paragraph RTL <span class="p s22">³</span> , so always ASCII 0-9

<div dir="rtl">

<span class="g s22">¹</span> گیت هاب استایل لینک شده را حذف میکند - GitHub strips the linked stylesheet, so the colors only exist locally

</div>

<div dir="rtl">

<span class="g s22">²</span> بدون فاصله توکن شناخته نمیشود - `copy¹` reads as an exponent, `copy ¹ ` is a gloss

</div>

<div dir="rtl">

<span class="g s22">³</span> رقم فارسی داخل بلوک عربی است - U+06F0 to U+06F9 belong to the Arabic block, one stray digit turns a whole English paragraph RTL

</div>

<details dir="rtl">
<summary>Why is fold content forced LTR?</summary>

<div dir="ltr">


A fold usually holds code or an answer, so the color stage wraps its body in a
`dir="ltr"` div. Persian prose inside a fold therefore stays left aligned.
Delete that one wrapper if you write prose folds.


</div>
</details>

<div dir="rtl">

## 4. Exercises (تمرین ها)

</div>

<div dir="rtl">

**Ex 1** - یک پاراگراف انگلیسی با یک واژه سخت بنویس و با پاورقی توضیح بده.

</div>

<details dir="rtl">
<summary>نمایش جواب</summary>

<div dir="ltr">


A view materializes one saved query <span class="p s22">¹</span> , so it costs storage but no recompute.

<span class="g s22">¹</span> the stored result trades disk for speed


</div>
</details>

<div dir="rtl">

**Ex 2** - همان پاراگراف را با ترجمه کامل فارسی بنویس و تعداد کاراکتر ها را مقایسه کن.

</div>

<details dir="rtl">
<summary>نمایش جواب</summary>

<div dir="ltr">


An inline translation costs 5 to 10 times the tokens of a gloss and breaks the
Latin run inside an RTL line. The gloss keeps both languages readable.


</div>
</details>

