# Generated by jeweler
# DO NOT EDIT THIS FILE DIRECTLY
# Instead, edit Jeweler::Tasks in Rakefile, and run the gemspec command
# -*- encoding: utf-8 -*-

Gem::Specification.new do |s|
  s.name = %q{gitian}
  s.version = "0.0.2"

  s.required_rubygems_version = Gem::Requirement.new(">= 1.3.5") if s.respond_to? :required_rubygems_version=
  s.authors = ["Miron Cuperman"]
  s.date = %q{2009-12-26}
  s.description = %q{Add the 'gitian' sub-commands to the gem command}
  s.email = %q{info.deb@nginz.org}
  s.files = [
    "lib/commands/abstract_gitian_command.rb",
     "lib/commands/gitian.rb",
     "lib/rubygems_plugin.rb"
  ]
  s.homepage = %q{https://gitian.org/}
  s.post_install_message = %q{
========================================================================

           Thanks for installing Gitian! You can now run:

    gem gitian        use Gitian.org or another distribution as your main gem source

========================================================================

}
  s.rdoc_options = ["--charset=UTF-8"]
  s.require_paths = ["lib"]
  s.rubyforge_project = %q{gitian-tools}
  s.rubygems_version = %q{1.3.5}
  s.summary = %q{Use a Gitian repository as the rubygems source}
  s.test_files = [
    "spec/spec_helper.rb",
     "spec/commands/gitian_spec.rb"
  ]

  if s.respond_to? :specification_version then
    current_version = Gem::Specification::CURRENT_SPECIFICATION_VERSION
    s.specification_version = 3

    if Gem::Version.new(Gem::RubyGemsVersion) >= Gem::Version.new('1.2.0') then
      s.add_development_dependency(%q<rspec>, [">= 1.2.0"])
    else
      s.add_dependency(%q<rspec>, [">= 1.2.0"])
    end
  else
    s.add_dependency(%q<rspec>, [">= 1.2.0"])
  end
end

