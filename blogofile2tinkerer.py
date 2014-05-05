from __future__ import unicode_literals

if __name__ == '__main__':
    import blogofile2tinkerer
    raise SystemExit(blogofile2tinkerer.main())

from datetime import datetime

from twisted.python.filepath import FilePath

from html2rst import html2text

HEADER_TEMPLATE = """\
%(title)s
%(underbar)s

.. author:: %(author)s
.. categories:: %(categories)s
.. tags:: %(tags)s
.. comments: %(comments)s
"""

SITEMAP = """\
Sitemap
=======

.. toctree::
   :maxdepth: 1

%(entries)s
"""

# input
posts = FilePath(b"_posts")

# output
blog = FilePath(b".")

def main():
    entries = []
    for post in posts.children():
        data = post.getContent().decode("utf-8")
        ignored, header, body = data.split(b"---", 2)
        meta = dict((text.strip() for text in line.split(":", 1)) for line in header.splitlines() if line.strip())
        date = datetime.strptime(meta["date"], "%Y/%m/%d %H:%M:%S")

        parent = blog.preauthChild(
            ("%d/%02d/%02d" % (date.year, date.month, date.day)).encode("utf-8"))
        title = filter(
            lambda ch: ch.isalpha() or ch == " ",
            meta["title"].strip().lower()).replace(" ", "_")
        entry = parent.child((title + ".rst").encode("utf-8"))

        header = HEADER_TEMPLATE % dict(
            author=meta["author"].strip(), categories="none",
            tags=meta["categories"].strip(), comments="",
            title=meta["title"].strip(),
            underbar="=" * len(meta["title"].strip()))

        if not parent.isdir():
            parent.makedirs()

        entry.setContent((header + html2text(body)).encode("utf-8"))

        entries.append(entry)

    entries.sort()
    entries.reverse()

    sitemap = SITEMAP % dict(
        entries="".join([
                "\n   " + "/".join(entry.segmentsFrom(blog))
                for entry in entries]))
    FilePath("master.rst").setContent(sitemap.encode("utf-8"))
