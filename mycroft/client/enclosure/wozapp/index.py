import tornado.web
import tornado.ioloop

class basicRequestHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!")

class staticRequestHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

if __name__ == "__main__":
    app = tornado.web.Application([
        (r"/", basicRequestHandler),
        (r"/tama", staticRequestHandler)

    ])

    app.listen(8881)
    print("I am listning on port 8881")
    tornado.ioloop.IOLoop.current().start()
