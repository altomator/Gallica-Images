#!/usr/bin/perl -w

# # Generates IIIF images from a list of Gallica identifiers:
# Format: : document_id/page_number
#Format:
#   ark:/12148/btv1b69366367/f1
#   ark:/12148/btv1b69366367/f3
#   ...
# Notes:
# Images are extracted at a % of their size.
# Use IIIF Image API version 3

use warnings;
use 5.010;
use LWP::Simple;
use Data::Dumper;
use warnings;

binmode(STDOUT, ":utf8");

# output directory for extracted images
my $OUT = "IMG";
# URL of Gallica IIIF v3 endpoint
my $iiif="https://openapi.bnf.fr/iiif/image/v3/ark:/12148/";

my $fic;
my $nbURL=0;
my $nbIMG=0;

# main
if(scalar(@ARGV)!=2){
	die "Usage: perl extraireIIIF.pl IDs_file \%ratio
	";
}
while(@ARGV){
	$fic=shift;
	$ratio=shift;
	if(-e $fic){
		print "...reading file $fic\n";
	}
	else{
		die "## $fic doesn't exists! ##\n";
	}
}

if(-d $OUT){
		say "Writing in $OUT...";
	}
	else{
		mkdir ($OUT) || die ("###  Can't create folder $OUT!  ###\n");
    say "Making folder $OUT...";
	}

open(FIC, "$fic") or die "## no file $fic! ##\n";
print "...\n";

my $txt;
while(<FIC>){
	$txt=$_;
  $nbURL++;
	say "\n - $nbURL -";
	$nbIMG=$nbIMG + genereIMG($txt);
}

print "\n\t$nbURL IDs analysed\n";
print "\t$nbIMG images generated\n";

close FIC;
print "=============================\n";



# ----------------------
sub genereIMG {
	my $ligne=shift;

  chop($ligne);
	# we get the ark+page number:  ark:/12148/btv1b69366367-f1
  my $ark = $ligne;
	# now we need to build the ark: btv1b69366367
  my @x = split("-f",$ark);
	$ark = $x[0];
	$page = $x[1];
  print " ARK: $ark";
	my $nomFic = $OUT."/".$ligne.".jpg";
  print "\n file: $nomFic";
	if (-e $nomFic) {
	   print("\n ! already exists !");
		 return 0
  }
  # we use a width IIIF parameter
	my $URL = $iiif.$ark."/f".$page."/full/pct:$ratio/0/default.jpg";
  print "\nURL: $URL";

  $cmd="curl '$URL'";
  my $content = `$cmd`;
  if (defined $content){
  		open my $fh, '>', $nomFic;
  		binmode $fh;
  		print {$fh} $content;
  		close $fh;
  		print "--> OK : $nomFic\n";
    return 1;}

   else {
  	print "## Ko URL! ##\n";
  	return 0;
  }
}
