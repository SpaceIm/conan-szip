import os

from conans import ConanFile, CMake, tools

class SzipConan(ConanFile):
    name = "szip"
    description = "Implementation of the extended-Rice lossless compression algorithm."
    license = "Szip License"
    topics = ("conan", "szip", "compression", "decompression")
    homepage = "https://support.hdfgroup.org/doc_resource/SZIP/"
    url = "https://github.com/conan-io/conan-center-index"
    exports_sources = "CMakeLists.txt"
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_encoding": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_encoding": False
    }

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(self.name + "-" + self.version, self._source_subfolder)

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def _patch_sources(self):
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "set (CMAKE_POSITION_INDEPENDENT_CODE ON)", "")
        tools.replace_in_file(os.path.join(self._source_subfolder, "src", "CMakeLists.txt"),
                              "add_library (${SZIP_LIB_TARGET} STATIC ${SZIP_SRCS} ${SZIP_PUBLIC_HEADERS})",
                              "if (NOT BUILD_SHARED_LIBS)\n" \
                              "add_library (${SZIP_LIB_TARGET} STATIC ${SZIP_SRCS} ${SZIP_PUBLIC_HEADERS})")
        tools.replace_in_file(os.path.join(self._source_subfolder, "src", "CMakeLists.txt"),
                              "if (BUILD_SHARED_LIBS)\n" \
                              "  add_library (${SZIP_LIBSH_TARGET} SHARED ${SZIP_SRCS} ${SZIP_PUBLIC_HEADERS})",
                              "else()\n" \
                              "  add_library (${SZIP_LIBSH_TARGET} SHARED ${SZIP_SRCS} ${SZIP_PUBLIC_HEADERS})")
        tools.replace_in_file(os.path.join(self._source_subfolder, "src", "CMakeLists.txt"),
                              "INSTALL_TARGET_PDB (${SZIP_LIB_TARGET} ${SZIP_INSTALL_BIN_DIR} libraries)",
                              "if (NOT BUILD_SHARED_LIBS)\n" \
                              "  INSTALL_TARGET_PDB (${SZIP_LIB_TARGET} ${SZIP_INSTALL_BIN_DIR} libraries)\n" \
                              "endif()")
        tools.replace_in_file(os.path.join(self._source_subfolder, "src", "szlib.h"),
                              "#define SZLIB_VERSION \"2.1.1\"",
                              "#include <stddef.h>\n" \
                              "#define SZLIB_VERSION \"2.1.1\"")

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["SZIP_ENABLE_ENCODING"] = self.options.enable_encoding
        self._cmake.definitions["SZIP_EXTERNALLY_CONFIGURED"] = True
        self._cmake.definitions["BUILD_TESTING"] = False
        self._cmake.definitions["SZIP_BUILD_FRAMEWORKS"] = False
        self._cmake.definitions["SZIP_PACK_MACOSX_FRAMEWORK"] = False
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
