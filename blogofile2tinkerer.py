from __future__ import unicode_literals

if __name__ == '__main__':
    from sys import argv
    import blogofile2tinkerer
    raise SystemExit(blogofile2tinkerer.main(argv))

from datetime import datetime
from subprocess import PIPE, Popen

from twisted.python.filepath import FilePath

HEADER_TEMPLATE = """\
%(title)s
%(underbar)s

.. author:: %(author)s
.. categories:: %(categories)s
.. tags:: %(tags)s
.. comments::

"""

SITEMAP = """\
Sitemap
=======

.. toctree::
   :maxdepth: 1

%(entries)s
"""

def fixpath(segment):
    return filter(lambda ch: ch.isalpha() or ch == b" ", segment).replace(b" ", b"_")


def main(argv):
    # input
    posts = FilePath(argv[1])

    # output
    blog = FilePath(argv[2])

    # Since Sphinx gets confused by image paths with "special" characters in
    # them, generate new names for all the image paths and a mapping from the
    # old names to the new names.
    images = FilePath(argv[3])

    imagepaths = []
    for post in images.children():
        if post.isdir():
            imagepaths.append(post)
            safe = post.sibling(fixpath(post.basename()))
            if post != safe and not safe.isdir():
                post.moveTo(safe)
                safe.linkTo(post)

    entries = []
    for post in posts.children():
        data = post.getContent().decode("utf-8")
        ignored, header, body = data.split(b"---", 2)
        meta = dict((text.strip() for text in line.split(":", 1)) for line in header.splitlines() if line.strip())
        date = datetime.strptime(meta["date"], "%Y/%m/%d %H:%M:%S")

        parent = blog.preauthChild(
            ("%d/%02d/%02d" % (date.year, date.month, date.day)).encode("utf-8"))
        title = fixpath(meta["title"].strip().lower().encode("utf-8")).decode("utf-8")
        entry = parent.child((title + ".rst").encode("utf-8"))

        header = HEADER_TEMPLATE % dict(
            author=meta["author"].strip(), categories="none",
            tags=meta["categories"].strip(), title=meta["title"].strip(),
            underbar="=" * len(meta["title"].strip()))

        for path in imagepaths:
            body = body.replace(
                u"/" + path.basename().decode("utf-8") + u"/",
                u"/" + fixpath(path.basename()).decode("utf-8") + u"/")

        if not parent.isdir():
            parent.makedirs()

        entry.setContent((header + html2rst(body)).encode("utf-8"))

        entries.append(entry)

    entries.sort()
    entries.reverse()

    sitemap = SITEMAP % dict(
        entries="".join([
                "\n   " + "/".join(entry.segmentsFrom(blog))
                for entry in entries]))
    blog.child(b"master.rst").setContent(sitemap.encode("utf-8"))

    FilePath(b"conf.py").copyTo(blog.child(b"conf.py"))


def html2rst(html):
    process = Popen([b"pandoc", b"--from=html", b"--to=rst"], stdin=PIPE, stdout=PIPE)
    process.stdin.write(html.encode("utf-8"))
    process.stdin.close()
    rst = process.stdout.read().decode("utf-8")
    process.wait()
    return rst
