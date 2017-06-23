from conans import ConanFile, CMake
import os


channel = os.getenv("CONAN_CHANNEL", "testing")
username = os.getenv("CONAN_USERNAME", "tleach")


class BoostTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    requires = "Boost/1.63.0@%s/%s" % (username, channel)
    generators = "cmake"

    def build(self):
        cmake = CMake(self)

        self.run('cmake "%s" %s' % (
                 self.conanfile_directory,
                 cmake.command_line
                 ))
        self.run("cmake --build . %s" % cmake.build_config)

    def test(self):
        print "Testing..."
        data_file = os.path.join(self.conanfile_directory, "data.txt")
        self.run("cd bin && .%slambda < %s" % (os.sep, data_file))
