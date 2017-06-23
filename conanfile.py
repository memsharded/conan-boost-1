from conans import ConanFile, tools
import os


class BoostConan(ConanFile):
    name = "Boost"
    version = "1.63.0"
    settings = "os", "arch", "compiler", "build_type"
    FOLDER_NAME = "boost_%s" % version.replace(".", "_")

    options = {
        "fPIC": [True, False],
        "shared": [True, False]
    }
    default_options = "fPIC=True", "shared=False"

    exports = ["FindBoost.cmake", "OriginalFindBoost*"]
    license = "Boost Software License - Version 1.0. \
        http://www.boost.org/LICENSE_1_0.txt"
    short_paths = True
    build_policy = "never"

    def config_options(self):
        """ First configuration step. Only settings are defined.
            Options can be removed according to these settings
        """
        if self.settings.compiler == "Visual Studio":
            self.options.remove("fPIC")

    def configure(self):
        """ Second configuration step. Both settings and options
            have values, in this case we can force static library
            if MT was specified as runtime
        """
        if self.settings.compiler == "Visual Studio" and \
           self.options.shared and "MT" in str(self.settings.compiler.runtime):
            self.options.shared = False

    def source(self):
        zip_name = "%s.tar.gz" % self.FOLDER_NAME

        base_url = "https://sourceforge.net/projects/boost/files/boost/"
        url = base_url + "%s/%s" % (self.version, zip_name)

        tools.download(url, zip_name)
        tools.unzip(zip_name, ".")
        os.unlink(zip_name)

    def build(self):
        if self.settings.os == "Windows":
            command = "bootstrap"
        else:
            command = "./bootstrap.sh"

        flags = []
        if self.settings.os == "Windows" and self.settings.compiler == "gcc":
            command += " mingw"
            flags.append("--layout=system")

        try:
            self.run("cd %s && %s" % (self.FOLDER_NAME, command))
        except:
            self.run("cd %s && type bootstrap.log" % self.FOLDER_NAME
                     if self.settings.os == "Windows"
                     else "cd %s && cat bootstrap.log" % self.FOLDER_NAME)
            raise

        if self.settings.compiler == "Visual Studio":
            flags.append("toolset=msvc-%s.0" % self.settings.compiler.version)
        elif str(self.settings.compiler) in ["clang", "gcc"]:
            flags.append("toolset=%s" % self.settings.compiler)

        flags.append("link=static")
        if self.settings.compiler == "Visual Studio" and self.settings.compiler.runtime: # NOQA
            flags.append("runtime-link=%s" % ("static" if "MT" in str(self.settings.compiler.runtime) else "shared")) # NOQA
        flags.append("variant=%s" % str(self.settings.build_type).lower())
        flags.append("address-model=%s" % ("32" if self.settings.arch == "x86" else "64")) # NOQA

        cxx_flags = []

        # fPIC DEFINITION
        if self.settings.compiler != "Visual Studio":
            if self.options.fPIC:
                cxx_flags.append("-fPIC")

        # LIBCXX DEFINITION FOR BOOST B2
        try:
            if str(self.settings.compiler.libcxx) == "libstdc++":
                flags.append("define=_GLIBCXX_USE_CXX11_ABI=0")
            elif str(self.settings.compiler.libcxx) == "libstdc++11":
                flags.append("define=_GLIBCXX_USE_CXX11_ABI=1")
            if "clang" in str(self.settings.compiler):
                if str(self.settings.compiler.libcxx) == "libc++":
                    cxx_flags.append("-stdlib=libc++")
                    cxx_flags.append("-std=c++11")
                    flags.append('linkflags="-stdlib=libc++"')
                else:
                    cxx_flags.append("-stdlib=libstdc++")
                    cxx_flags.append("-std=c++11")
        except:
            pass

        cxx_flags = 'cxxflags="%s"' % " ".join(cxx_flags) if cxx_flags else ""
        flags.append(cxx_flags)

        # JOIN ALL FLAGS
        b2_flags = " ".join(flags)

        command = "b2" if self.settings.os == "Windows" else "./b2"
        hardcode_params = "--abbreviate-paths --without-python"

        full_command = "cd %s && %s %s -j%s %s" % (
            self.FOLDER_NAME,
            command,
            b2_flags,
            tools.cpu_count(),
            hardcode_params
        )
        self.output.warn(full_command)
        self.run(full_command)

    def package(self):
        self.copy("FindBoost.cmake", ".", ".")
        self.copy("OriginalFindBoost*", ".", ".")

        self.copy(pattern="*", dst="include/boost", src="%s/boost" % self.FOLDER_NAME) # NOQA
        self.copy(pattern="*.a", dst="lib", src="%s/stage/lib" % self.FOLDER_NAME) # NOQA

        # self.copy(pattern="*.dylib*", dst="lib", src="%s/stage/lib" % self.FOLDER_NAME) # NOQA
        self.copy(pattern="*.lib", dst="lib", src="%s/stage/lib" % self.FOLDER_NAME) # NOQA
        # self.copy(pattern="*.dll", dst="bin", src="%s/stage/lib" % self.FOLDER_NAME) # NOQA

    def package_info(self):
        self.cpp_info.defines.append("BOOST_USE_STATIC_LIBS")

        libs = ("wave unit_test_framework prg_exec_monitor test_exec_monitor "
                "container exception graph iostreams locale log log_setup "
                "math_c99 math_c99f math_c99l math_tr1 math_tr1f math_tr1l "
                "program_options random regex wserialization serialization "
                "signals coroutine context timer thread chrono date_time "
                "atomic filesystem system").split()

        if self.settings.compiler != "Visual Studio":
            self.cpp_info.libs.extend(["boost_%s" % lib for lib in libs])
        else:
            win_libs = []
            # http://www.boost.org/doc/libs/1_55_0/more/getting_started/windows.html
            visual_version = int(str(self.settings.compiler.version)) * 10
            runtime = str(self.settings.compiler.runtime).lower()

            abi_tags = []
            if self.settings.compiler.runtime in ("MTd", "MT"):
                abi_tags.append("s")

            if self.settings.build_type == "Debug":
                abi_tags.append("gd")

            abi_tags = ("-%s" % "".join(abi_tags)) if abi_tags else ""

            version = "_".join(self.version.split(".")[0:2])
            suffix = "vc%d-%s%s-%s" % (
                visual_version,
                runtime,
                abi_tags,
                version
            )
            prefix = "lib" if not self.options.shared else ""

            win_libs.extend(["%sboost_%s-%s" % (prefix, lib, suffix) for lib in libs if lib not in ["exception", "test_exec_monitor"]]) # NOQA
            win_libs.extend(["libboost_%s-%s" % (lib, suffix) for lib in libs if lib in ["exception", "test_exec_monitor"]]) # NOQA

            self.output.warn("EXPORTED BOOST LIBRARIES: %s" % win_libs)
            self.cpp_info.libs.extend(win_libs)
            # DISABLES AUTO LINKING! NO SMART AND MAGIC DECISIONS THANKS!
            self.cpp_info.defines.extend(["BOOST_ALL_NO_LIB"])
