#include <iostream>
#include <enoki/array.h>

/* Don't forget to include the 'enoki' namespace */
using namespace enoki;

int main()
{
    using StrArray = Array<std::string, 2>;

    StrArray x("Hello ", "How are "),
	     y("world!", "you?");

    // Prints: "[Hello world!,  How are you?]"
    std::cout << x + y << std::endl;
}
